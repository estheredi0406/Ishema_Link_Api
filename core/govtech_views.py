"""
Government API Integration Views
Mock endpoints for RRA, RURA, and EAC Customs
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.http import HttpResponse

from .govtech_services import RRAConnector, RURAConnector, EACCustomsConnector
from payments.models import Payment
from django.utils import timezone


@extend_schema(
    summary="Sign payment receipt with RRA EBM",
    description="Request electronic billing machine signature from Rwanda Revenue Authority",
    tags=['Government Integration'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'payment_id': {'type': 'integer'},
                'amount': {'type': 'number'},
                'merchant_tin': {'type': 'string'}
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ebm_sign_receipt(request):
    """
    POST /api/gov/ebm/sign-receipt/
    
    Request tax receipt signature from RRA Electronic Billing Machine
    
    Every payment must be signed by RRA for tax compliance
    """
    payment_id = request.data.get('payment_id')
    amount = request.data.get('amount')
    merchant_tin = request.data.get('merchant_tin', 'TIN123456789')
    
    if not payment_id or not amount:
        return Response({
            'success': False,
            'error': 'Missing required fields: payment_id and amount'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get payment record
        payment = Payment.objects.get(id=payment_id)
        
        # Verify amount matches
        if float(amount) != float(payment.amount):
            return Response({
                'success': False,
                'error': 'Amount mismatch with payment record'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Call RRA EBM service
        receipt = RRAConnector.sign_receipt(
            payment_id=payment_id,
            amount=amount,
            merchant_tin=merchant_tin
        )
        
        return Response(receipt, status=status.HTTP_200_OK)
        
    except Payment.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Payment {payment_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Verify driver license with RURA",
    description="Check if driver license and vehicle insurance are valid",
    tags=['Government Integration'],
    parameters=[
        OpenApiParameter(
            name='license_no',
            type=str,
            location=OpenApiParameter.PATH,
            description='Driver license number (format: RADXXXXXX)'
        )
    ]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rura_verify_license(request, license_no):
    """
    GET /api/gov/rura/verify-license/{license_no}/
    
    Verify driver license and vehicle insurance with RURA
    
    System must check this BEFORE assigning a driver to prevent
    unlicensed/uninsured vehicles from operating
    """
    try:
        # Call RURA verification service
        verification = RURAConnector.verify_license(license_no)
        
        if not verification.get('success'):
            return Response(verification, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if license is valid
        if verification.get('status') in ['EXPIRED', 'NOT_FOUND']:
            return Response({
                **verification,
                'can_operate': False,
                'blocking_reason': f"License {verification.get('status').lower()} - cannot assign driver"
            }, status=status.HTTP_200_OK)
        
        # Check insurance
        if not verification.get('insurance_valid'):
            return Response({
                **verification,
                'can_operate': False,
                'blocking_reason': 'Vehicle insurance expired or invalid'
            }, status=status.HTTP_200_OK)
        
        return Response({
            **verification,
            'can_operate': True
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Generate EAC customs manifest",
    description="Create customs manifest XML for international shipments",
    tags=['Government Integration'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'shipment_id': {'type': 'integer'},
                'destination_country': {'type': 'string'},
                'cargo_value': {'type': 'number'}
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def customs_generate_manifest(request):
    """
    POST /api/gov/customs/generate-manifest/
    
    Generate EAC-compliant customs manifest XML
    
    Required for all international shipments crossing borders
    """
    shipment_id = request.data.get('shipment_id')
    
    if not shipment_id:
        return Response({
            'success': False,
            'error': 'Missing required field: shipment_id'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from domestic.models import DomesticShipment
        shipment = DomesticShipment.objects.get(id=shipment_id)
        
        # Prepare shipment data for manifest
        shipment_data = {
            'shipment_id': shipment_id,
            'sender_name': shipment.sender.get_full_name() if shipment.sender else 'Unknown',
            'sender_address': f"{shipment.origin_sector}, {shipment.origin_district}, Rwanda",
            'sender_phone': shipment.sender_phone,
            'receiver_name': shipment.receiver_name,
            'receiver_address': shipment.delivery_address,
            'receiver_phone': shipment.receiver_phone,
            'description': shipment.description or 'General Goods',
            'weight': float(shipment.weight),
            'cargo_value': float(request.data.get('cargo_value', shipment.price)),
            'destination_country': request.data.get('destination_country', 'UG'),
            'transport_mode': shipment.transport_mode,
            'vehicle_plate': 'RAD 000 A',  # Would come from assigned driver
            'driver_name': 'Driver Name',   # Would come from assigned driver
            'hs_code': request.data.get('hs_code', '9999.99.99')
        }
        
        # Generate manifest
        manifest = EACCustomsConnector.generate_manifest(shipment_data)
        
        return Response(manifest, status=status.HTTP_200_OK)
        
    except DomesticShipment.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Shipment {shipment_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Download customs manifest XML",
    description="Download generated manifest as XML file",
    tags=['Government Integration']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_manifest_xml(request, manifest_id):
    """
    GET /api/gov/customs/manifest/{manifest_id}/download/
    
    Download customs manifest XML file
    """
    # In production, would retrieve from database
    # For now, return sample
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<CustomsManifest version="2.0" xmlns="http://www.eac.int/customs">
  <Header>
    <ManifestID>{manifest_id}</ManifestID>
    <IssueDate>{timezone.now().isoformat()}</IssueDate>
  </Header>
</CustomsManifest>"""
    
    response = HttpResponse(xml_content, content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="manifest_{manifest_id}.xml"'
    return response