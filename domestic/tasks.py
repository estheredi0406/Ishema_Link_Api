"""
Celery Tasks for Domestic Shipments
Async tasks for notifications and status updates
"""
import logging
from celery import shared_task
from django.utils import timezone
from core.notifications import NotificationService
from .models import DomesticShipment, ShipmentLog

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_shipment_notification_task(self, shipment_id: int, notify_sender: bool = True, notify_receiver: bool = True):
    """
    Send SMS notification about shipment status change
    
    Args:
        self: Celery task instance
        shipment_id: ID of the shipment
        notify_sender: Whether to notify sender
        notify_receiver: Whether to notify receiver
        
    Returns:
        Dict with notification results
    """
    try:
        logger.info(f"🚀 Starting notification task for shipment ID: {shipment_id}")
        
        # Get shipment
        shipment = DomesticShipment.objects.get(id=shipment_id)
        
        results = {
            'shipment_tracking': shipment.tracking_code,
            'status': shipment.status,
            'notifications_sent': []
        }
        
        # Notify sender
        if notify_sender and shipment.sender_phone:
            try:
                sender_result = NotificationService.send_shipment_notification(
                    shipment_tracking=shipment.tracking_code,
                    phone=shipment.sender_phone,
                    status=shipment.status,
                    recipient_name=shipment.sender.username
                )
                results['notifications_sent'].append({
                    'type': 'sender_sms',
                    'success': sender_result['success'],
                    'recipient': shipment.sender_phone
                })
            except Exception as e:
                logger.error(f"Failed to notify sender: {e}")
        
        # Notify receiver
        if notify_receiver and shipment.receiver_phone:
            try:
                receiver_result = NotificationService.send_shipment_notification(
                    shipment_tracking=shipment.tracking_code,
                    phone=shipment.receiver_phone,
                    status=shipment.status,
                    recipient_name=shipment.receiver_name
                )
                results['notifications_sent'].append({
                    'type': 'receiver_sms',
                    'success': receiver_result['success'],
                    'recipient': shipment.receiver_phone
                })
            except Exception as e:
                logger.error(f"Failed to notify receiver: {e}")
        
        logger.info(f"✅ Notification task completed for {shipment.tracking_code}")
        return results
        
    except DomesticShipment.DoesNotExist:
        logger.error(f"Shipment {shipment_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error in notification task: {e}")
        # Retry the task (up to 3 times)
        raise self.retry(exc=e, countdown=60)


@shared_task
def update_shipment_status_task(shipment_id: int, new_status: str, location: str = "", notes: str = ""):
    """
    Update shipment status asynchronously
    Creates tracking log and triggers notifications
    
    Args:
        shipment_id: ID of the shipment
        new_status: New status to set
        location: Current location (optional)
        notes: Additional notes (optional)
        
    Returns:
        Dict with update results
    """
    try:
        logger.info(f"📦 Updating shipment {shipment_id} to status: {new_status}")
        
        shipment = DomesticShipment.objects.get(id=shipment_id)
        old_status = shipment.status
        
        # Update shipment status
        shipment.status = new_status
        
        # Update special timestamps
        if new_status == 'PICKED_UP' and not shipment.picked_up_at:
            shipment.picked_up_at = timezone.now()
        elif new_status == 'DELIVERED' and not shipment.delivered_at:
            shipment.delivered_at = timezone.now()
        
        shipment.save()
        
        # Create tracking log
        log = ShipmentLog.objects.create(
            shipment=shipment,
            status=new_status,
            location=location,
            notes=notes or f"Status changed from {old_status} to {new_status}"
        )
        
        logger.info(f"✅ Shipment {shipment.tracking_code} updated to {new_status}")
        
        # Trigger notification (async)
        send_shipment_notification_task.delay(shipment_id)
        
        return {
            'success': True,
            'tracking_code': shipment.tracking_code,
            'old_status': old_status,
            'new_status': new_status,
            'log_id': log.id
        }
        
    except DomesticShipment.DoesNotExist:
        logger.error(f"Shipment {shipment_id} not found")
        return {'success': False, 'error': 'Shipment not found'}
    except Exception as e:
        logger.error(f"Error updating shipment: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def batch_update_shipments_task(shipment_ids: list, new_status: str):
    """
    Update multiple shipments at once
    Useful for bulk operations (e.g., all packages arriving at hub)
    
    Args:
        shipment_ids: List of shipment IDs
        new_status: Status to apply to all
        
    Returns:
        Summary of batch update
    """
    logger.info(f"📋 Batch updating {len(shipment_ids)} shipments to {new_status}")
    
    results = {
        'total': len(shipment_ids),
        'successful': 0,
        'failed': 0,
        'errors': []
    }
    
    for shipment_id in shipment_ids:
        try:
            result = update_shipment_status_task(
                shipment_id=shipment_id,
                new_status=new_status,
                notes=f"Batch update to {new_status}"
            )
            
            if result.get('success'):
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"Shipment {shipment_id}: {result.get('error')}")
                
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"Shipment {shipment_id}: {str(e)}")
    
    logger.info(f"✅ Batch update complete: {results['successful']}/{results['total']} successful")
    return results