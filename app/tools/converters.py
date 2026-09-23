def rupees_to_paise(rupees: float) -> int:
    """Convert INR rupees to integer paise without float precision loss.
    
    Args:
        rupees: Amount in Indian Rupees (e.g. 500.50)
        
    Returns:
        int: Amount in paise (e.g. 50050)
        
    Raises:
        ValueError: If amount is negative or exceeds maximum financial bounds.
    """
    if rupees < 0:
        raise ValueError("Monetary amount cannot be negative.")
    if rupees > 10_000_000.0:  # Max 1 Crore INR sanity check
        raise ValueError("Monetary amount exceeds system limit of ₹10,000,000.")
    return int(round(rupees * 100))


def paise_to_rupees(paise: int) -> float:
    """Convert integer paise to INR rupees.
    
    Args:
        paise: Amount in paise (e.g. 50050)
        
    Returns:
        float: Amount in Indian Rupees (e.g. 500.50)
        
    Raises:
        ValueError: If paise is negative.
    """
    if paise < 0:
        raise ValueError("Paise cannot be negative.")
    return round(paise / 100.0, 2)
