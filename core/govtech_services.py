"""
GovTech Mock Services
Simulates integration with Rwanda Government APIs
"""
import hashlib
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import xml.etree.ElementTree as ET
from xml.dom import minidom


class RRAConnector:
    """
    Rwanda Revenue Authority (RRA) Mock Connector
    Simulates Electronic Billing Machine (EBM) integration
    """
    
    @staticmethod
    def sign_receipt(payment_id, amount, merchant_tin=None):
        """
        Generate EBM receipt signature
        
        In production, this would call:
        POST https://ebm.rra.gov.rw/api/v1/sign-receipt
        
        Args:
            payment_id: Payment transaction ID
            amount: Payment amount in RWF
            merchant_tin: Tax Identification Number
        
        Returns:
            dict: EBM receipt with digital signature
        """
        # Calculate tax (18% VAT in Rwanda)
        tax_rate = Decimal('0.18')
        amount_decimal = Decimal(str(amount))
        tax_amount = amount_decimal * tax_rate
        total_with_tax = amount_decimal + tax_amount
        
        # Generate mock receipt number (format: EBM-YEAR-SEQUENCE)
        receipt_number = f"EBM-{datetime.now().year}-{str(payment_id).zfill(6)}"
        
        # Generate mock digital signature
        signature_base = f"{receipt_number}{amount}{merchant_tin}{datetime.now().isoformat()}"
        signature = hashlib.sha256(signature_base.encode()).hexdigest()[:32].upper()
        
        return {
            'success': True,
            'receipt_number': receipt_number,
            'signature': signature,
            'payment_id': payment_id,
            'amount': float(amount_decimal),
            'tax_amount': float(tax_amount),
            'total_amount': float(total_with_tax),
            'tax_rate': '18%',
            'merchant_tin': merchant_tin or 'TIN123456789',
            'timestamp': datetime.now().isoformat(),
            'status': 'SIGNED',
            'message': 'Receipt signed successfully by RRA EBM'
        }
    
    @staticmethod
    def verify_receipt(receipt_number):
        """
        Verify EBM receipt authenticity
        
        Args:
            receipt_number: EBM receipt number
        
        Returns:
            dict: Verification status
        """
        # In production, would verify against RRA database
        return {
            'valid': True,
            'receipt_number': receipt_number,
            'status': 'VERIFIED',
            'message': 'Receipt is authentic'
        }


class RURAConnector:
    """
    Rwanda Utilities Regulatory Authority (RURA) Mock Connector
    Simulates transport license verification
    """
    
    # Mock database of valid licenses
    MOCK_LICENSES = {
        'RAD123456': {
            'driver_name': 'Jean UWIMANA',
            'vehicle_plate': 'RAD 123 A',
            'status': 'VALID',
            'insurance_valid': True,
            'insurance_expires': (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
            'expires_at': '2027-12-31'
        },
        'RAD789012': {
            'driver_name': 'Marie MUGABE',
            'vehicle_plate': 'RAD 789 B',
            'status': 'VALID',
            'insurance_valid': True,
            'insurance_expires': (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'),
            'expires_at': '2027-06-30'
        },
        'RAD999999': {
            'driver_name': 'Paul HABIMANA',
            'vehicle_plate': 'RAD 999 C',
            'status': 'EXPIRED',
            'insurance_valid': False,
            'insurance_expires': '2025-01-15',
            'expires_at': '2025-01-15'
        }
    }
    
    @staticmethod
    def verify_license(license_number):
        """
        Verify driver license and vehicle insurance
        
        In production, this would call:
        GET https://rura.gov.rw/api/v1/verify-license/{license_number}
        
        Args:
            license_number: Driver license number (format: RADXXXXXX)
        
        Returns:
            dict: License verification result
        """
        # Validate license format
        if not license_number or len(license_number) < 6:
            return {
                'success': False,
                'error': 'Invalid license format',
                'message': 'License number must be at least 6 characters'
            }
        
        # Check if license exists in mock database
        license_data = RURAConnector.MOCK_LICENSES.get(license_number)
        
        if license_data:
            return {
                'success': True,
                'license_number': license_number,
                **license_data,
                'verified_at': datetime.now().isoformat(),
                'message': f"License verified by RURA - Status: {license_data['status']}"
            }
        else:
            # License not found - generate random valid/invalid
            import random
            is_valid = random.choice([True, False])
            
            return {
                'success': True,
                'license_number': license_number,
                'driver_name': 'Unknown Driver',
                'vehicle_plate': 'RAD XXX X',
                'status': 'VALID' if is_valid else 'NOT_FOUND',
                'insurance_valid': is_valid,
                'insurance_expires': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d') if is_valid else 'N/A',
                'expires_at': '2027-12-31' if is_valid else 'N/A',
                'verified_at': datetime.now().isoformat(),
                'message': 'License not found in RURA database' if not is_valid else 'License verified'
            }


class EACCustomsConnector:
    """
    East African Community (EAC) Customs Mock Connector
    Generates customs manifests for international shipments
    """
    
    @staticmethod
    def generate_manifest(shipment_data):
        """
        Generate EAC-compliant customs manifest XML
        
        Args:
            shipment_data: dict with shipment details
        
        Returns:
            dict: Manifest ID and XML content
        """
        manifest_id = f"RW-{shipment_data.get('destination_country', 'XX')}-{datetime.now().year}-{uuid.uuid4().hex[:8].upper()}"
        
        # Create XML structure (EAC standard format)
        root = ET.Element('CustomsManifest')
        root.set('version', '2.0')
        root.set('xmlns', 'http://www.eac.int/customs')
        
        # Header
        header = ET.SubElement(root, 'Header')
        ET.SubElement(header, 'ManifestID').text = manifest_id
        ET.SubElement(header, 'IssueDate').text = datetime.now().isoformat()
        ET.SubElement(header, 'OriginCountry').text = 'RW'
        ET.SubElement(header, 'DestinationCountry').text = shipment_data.get('destination_country', 'UG')
        
        # Shipper
        shipper = ET.SubElement(root, 'Shipper')
        ET.SubElement(shipper, 'Name').text = shipment_data.get('sender_name', 'Unknown Sender')
        ET.SubElement(shipper, 'Address').text = shipment_data.get('sender_address', 'Kigali, Rwanda')
        ET.SubElement(shipper, 'Phone').text = shipment_data.get('sender_phone', '+250788000000')
        
        # Consignee
        consignee = ET.SubElement(root, 'Consignee')
        ET.SubElement(consignee, 'Name').text = shipment_data.get('receiver_name', 'Unknown Receiver')
        ET.SubElement(consignee, 'Address').text = shipment_data.get('receiver_address', 'Destination Address')
        ET.SubElement(consignee, 'Phone').text = shipment_data.get('receiver_phone', '+256700000000')
        
        # Cargo
        cargo = ET.SubElement(root, 'Cargo')
        ET.SubElement(cargo, 'Description').text = shipment_data.get('description', 'General Goods')
        ET.SubElement(cargo, 'Weight').text = str(shipment_data.get('weight', '0'))
        ET.SubElement(cargo, 'WeightUnit').text = 'KG'
        ET.SubElement(cargo, 'Value').text = str(shipment_data.get('cargo_value', '0'))
        ET.SubElement(cargo, 'Currency').text = 'RWF'
        ET.SubElement(cargo, 'HSCode').text = shipment_data.get('hs_code', '9999.99.99')
        
        # Transport
        transport = ET.SubElement(root, 'Transport')
        ET.SubElement(transport, 'Mode').text = shipment_data.get('transport_mode', 'ROAD')
        ET.SubElement(transport, 'VehicleRegistration').text = shipment_data.get('vehicle_plate', 'RAD 000 A')
        ET.SubElement(transport, 'DriverName').text = shipment_data.get('driver_name', 'Unknown Driver')
        
        # Convert to pretty XML string
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        
        return {
            'success': True,
            'manifest_id': manifest_id,
            'xml_content': xml_str,
            'format': 'EAC-COMESA-STANDARD-v2.0',
            'generated_at': datetime.now().isoformat(),
            'status': 'GENERATED',
            'message': 'Customs manifest generated successfully',
            'qr_code_data': f"MANIFEST:{manifest_id}"
        }