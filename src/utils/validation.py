def validate_portfolio_allocation(allocations):
    """Validate portfolio allocation format and constraints"""
    try:
        total = 0
        for token, amount in allocations.items():
            # Validate amount type
            if not isinstance(amount, (int, float)):
                print(f"❌ Invalid amount type for {token}: {type(amount)}")
                return False
                
            # Validate amount is positive
            if amount < 0:
                print(f"❌ Negative allocation for {token}: {amount}")
                return False
                
            total += amount
            
        # Check total allocation
        if total > config.usd_size:
            print(f"❌ Total allocation ${total} exceeds maximum ${config.usd_size}")
            return False
            
        # Validate USDC buffer
        usdc_amount = allocations.get(config.USDC_ADDRESS, 0)
        min_usdc = config.usd_size * (config.CASH_PERCENTAGE / 100)
        if usdc_amount < min_usdc:
            print(f"❌ USDC buffer ${usdc_amount} below minimum ${min_usdc}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error validating allocations: {e}")
        return False 