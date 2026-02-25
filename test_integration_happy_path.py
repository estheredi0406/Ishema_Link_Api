def test_user_cannot_view_other_users_shipments(self):
    """Users should only see their own shipments (privacy test)"""
    
    client = APIClient()
    
    # Create two users
    user1 = User.objects.create_user(
        phone='+250788222222',
        password='User1Pass123!',
        user_type='CUSTOMER',
        username='user1'
    )
    
    user2 = User.objects.create_user(
        phone='+250788333333',
        password='User2Pass123!',
        user_type='CUSTOMER',
        username='user2'
    )
    
    # User 1 creates a shipment (minimal fields only)
    shipment = DomesticShipment.objects.create(
        sender=user1,
        receiver_name='Receiver',
        receiver_phone='+250788444444',
        origin_district='KIGALI',
        destination_district='HUYE',
        description='Test item',
        weight=Decimal('10.00'),
        price=Decimal('5000.00')
    )
    
    # User 2 tries to access User 1's shipment
    client.force_authenticate(user=user2)
    response = client.get(f'/api/domestic/shipments/{shipment.id}/')
    
    # Should be forbidden or not found
    assert response.status_code in [403, 404]