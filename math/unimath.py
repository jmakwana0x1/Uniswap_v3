"""
Uniswap V3 Liquidity and Swap Calculations
===========================================
This script demonstrates:
1. Converting between prices, ticks, and square root prices
2. Calculating liquidity from token amounts
3. Simulating swaps and price movements
"""

import math

# ============================================
# CONSTANTS
# ============================================

# Tick range limits in Uniswap V3
# These are the absolute minimum and maximum ticks allowed
min_tick = -887272
max_tick = 887272

# Q96 fixed-point format constant
# We multiply prices by 2^96 to convert decimals to integers
# This allows precise calculations without floating point errors
q96 = 2**96

# Standard Ethereum unit (1 ETH = 10^18 wei)
# Used to convert between human-readable amounts and contract amounts
eth = 10**18


# ============================================
# CONVERSION FUNCTIONS
# ============================================

def price_to_tick(p):
    """
    Convert a price to its corresponding tick index.
    
    Formula: i = log_1.0001(P)
    This is equivalent to: i = ln(P) / ln(1.0001)
    
    Args:
        p: Price (e.g., 5000 means 1 ETH = 5000 USDC)
    
    Returns:
        Tick index (integer)
    
    Example:
        price_to_tick(5000) = 85176
    """
    return math.floor(math.log(p, 1.0001))


def price_to_sqrtp(p):
    """
    Convert a price to square root price in Q64.96 format.
    
    Steps:
    1. Take square root of price: √P
    2. Multiply by 2^96 to convert to Q64.96 format
    3. Convert to integer (smart contracts only work with integers)
    
    Args:
        p: Price (e.g., 5000)
    
    Returns:
        Square root price as integer in Q64.96 format
    
    Example:
        price_to_sqrtp(5000) = 5602277097478614198912276234240
    """
    return int(math.sqrt(p) * q96)


def sqrtp_to_price(sqrtp):
    """
    Convert square root price (Q64.96 format) back to regular price.
    
    Steps:
    1. Divide by 2^96 to convert from Q64.96 to decimal
    2. Square the result to get price: (√P)² = P
    
    Args:
        sqrtp: Square root price in Q64.96 format
    
    Returns:
        Regular price as decimal
    
    Example:
        sqrtp_to_price(5602277097478614198912276234240) ≈ 5000
    """
    return (sqrtp / q96) ** 2


def tick_to_sqrtp(t):
    """
    Convert a tick index to square root price in Q64.96 format.
    
    Formula: √P(i) = 1.0001^(i/2)
    
    Why i/2? Because we want √P, not P.
    If P(i) = 1.0001^i, then √P(i) = 1.0001^(i/2)
    
    Args:
        t: Tick index (e.g., 85176)
    
    Returns:
        Square root price in Q64.96 format
    """
    return int((1.0001 ** (t / 2)) * q96)


# ============================================
# LIQUIDITY CALCULATION FUNCTIONS
# ============================================

def liquidity0(amount, pa, pb):
    """
    Calculate liquidity (L) from token0 (e.g., ETH) amount.
    
    This is used for the LEFT side of the price curve (below current price).
    
    Formula: L = Δx × (√Pb × √Pa) / (√Pb - √Pa)
    
    Where:
        - Δx = amount of token0 (ETH)
        - Pa = lower sqrt price
        - Pb = upper sqrt price (higher than Pa)
    
    Args:
        amount: Amount of token0 in wei
        pa: Square root price A in Q64.96
        pb: Square root price B in Q64.96
    
    Returns:
        Liquidity value (L)
    
    Note: We ensure pa < pb by swapping if needed
    """
    # Ensure pa is lower than pb (swap if needed)
    if pa > pb:
        pa, pb = pb, pa
    
    # Calculate liquidity using the formula
    # Division by q96 is needed because pa * pb gives us a value in Q192 format
    return (amount * (pa * pb) / q96) / (pb - pa)


def liquidity1(amount, pa, pb):
    """
    Calculate liquidity (L) from token1 (e.g., USDC) amount.
    
    This is used for the RIGHT side of the price curve (above current price).
    
    Formula: L = Δy / (√Pb - √Pa)
    
    Where:
        - Δy = amount of token1 (USDC)
        - Pa = lower sqrt price
        - Pb = upper sqrt price
    
    Args:
        amount: Amount of token1 in wei
        pa: Square root price A in Q64.96
        pb: Square root price B in Q64.96
    
    Returns:
        Liquidity value (L)
    """
    # Ensure pa is lower than pb
    if pa > pb:
        pa, pb = pb, pa
    
    # Calculate liquidity using the formula
    # Multiply by q96 to maintain Q64.96 format precision
    return amount * q96 / (pb - pa)


# ============================================
# TOKEN AMOUNT CALCULATION FUNCTIONS
# ============================================

def calc_amount0(liq, pa, pb):
    """
    Calculate token0 (ETH) amount from liquidity.
    
    This is the INVERSE of liquidity0() - given L, find Δx.
    
    Formula: Δx = L × (√Pb - √Pa) / (√Pb × √Pa)
    
    Used to determine how much token0 is needed for a given liquidity.
    
    Args:
        liq: Liquidity value (L)
        pa: Square root price A in Q64.96
        pb: Square root price B in Q64.96
    
    Returns:
        Amount of token0 in wei
    """
    # Ensure pa < pb
    if pa > pb:
        pa, pb = pb, pa
    
    # Calculate token0 amount
    # We multiply by q96 then divide by both prices
    return int(liq * q96 * (pb - pa) / pb / pa)


def calc_amount1(liq, pa, pb):
    """
    Calculate token1 (USDC) amount from liquidity.
    
    This is the INVERSE of liquidity1() - given L, find Δy.
    
    Formula: Δy = L × (√Pb - √Pa)
    
    Used to determine how much token1 is needed for a given liquidity.
    
    Args:
        liq: Liquidity value (L)
        pa: Square root price A in Q64.96
        pb: Square root price B in Q64.96
    
    Returns:
        Amount of token1 in wei
    """
    # Ensure pa < pb
    if pa > pb:
        pa, pb = pb, pa
    
    # Calculate token1 amount
    # Divide by q96 to convert back from Q64.96 format
    return int(liq * (pb - pa) / q96)


# ============================================
# LIQUIDITY PROVISION EXAMPLE
# ============================================

print("=" * 60)
print("LIQUIDITY PROVISION EXAMPLE")
print("=" * 60)

# Define the price range for our liquidity position
price_low = 4545   # Lower bound: $4,545 per ETH
price_cur = 5000   # Current price: $5,000 per ETH
price_upp = 5500   # Upper bound: $5,500 per ETH

print(f"Price range: {price_low}-{price_upp}; current price: {price_cur}")

# Convert prices to square root prices in Q64.96 format
# These are the values the smart contract actually uses
sqrtp_low = price_to_sqrtp(price_low)  # √4545 in Q64.96
sqrtp_cur = price_to_sqrtp(price_cur)  # √5000 in Q64.96
sqrtp_upp = price_to_sqrtp(price_upp)  # √5500 in Q64.96

# Define how much we want to deposit
amount_eth = 1 * eth      # 1 ETH (in wei)
amount_usdc = 5000 * eth  # 5000 USDC (in wei, assuming 18 decimals)

# Calculate liquidity from ETH (for LEFT side of curve)
# This tells us how much liquidity our 1 ETH provides
liq0 = liquidity0(amount_eth, sqrtp_cur, sqrtp_upp)

# Calculate liquidity from USDC (for RIGHT side of curve)
# This tells us how much liquidity our 5000 USDC provides
liq1 = liquidity1(amount_usdc, sqrtp_cur, sqrtp_low)

# Choose the SMALLER liquidity value
# Why? Because we need BOTH tokens to provide liquidity
# The smaller value ensures we have enough of both tokens
liq = int(min(liq0, liq1))

print(f"Deposit: {amount_eth/eth} ETH, {amount_usdc/eth} USDC; liquidity: {liq}")

# ============================================
# SWAP EXAMPLE 1: Selling USDC for ETH
# ============================================
# When you sell USDC, you're BUYING ETH
# This makes the price of ETH go UP (more USDC per ETH)

print("\n" + "=" * 60)
print("SWAP 1: SELLING USDC FOR ETH")
print("=" * 60)

# We're selling 42 USDC
amount_in = 42 * eth

print(f"\nSelling {amount_in/eth} USDC")

# When we add USDC to the pool, the price goes UP
# Formula: Δ√P = Δy / L
# New √P = Current √P + (USDC amount / Liquidity)
price_diff = (amount_in * q96) // liq  # Price change in Q64.96 format
price_next = sqrtp_cur + price_diff    # New square root price

# Display the new price information
print("New price:", (price_next / q96) ** 2)  # Convert √P to P
print("New sqrtP:", price_next)
print("New tick:", price_to_tick((price_next / q96) ** 2))

# Calculate EXACT amounts for the swap
# These formulas ensure we move from sqrtp_cur to price_next
amount_in = calc_amount1(liq, price_next, sqrtp_cur)   # USDC in
amount_out = calc_amount0(liq, price_next, sqrtp_cur)  # ETH out

print("USDC in:", amount_in / eth)   # How much USDC goes in
print("ETH out:", amount_out / eth)  # How much ETH comes out

# ============================================
# SWAP EXAMPLE 2: Selling ETH for USDC
# ============================================
# When you sell ETH, you're BUYING USDC
# This makes the price of ETH go DOWN (less USDC per ETH)

print("\n" + "=" * 60)
print("SWAP 2: SELLING ETH FOR USDC")
print("=" * 60)

# We're selling 0.01337 ETH
amount_in = 0.01337 * eth

print(f"\nSelling {amount_in/eth} ETH")

# When we add ETH to the pool, the price goes DOWN
# Formula is more complex because we're dealing with token0
# New √P = (L × √P) / (L + Δx × √P)
price_next = int((liq * q96 * sqrtp_cur) // (liq * q96 + amount_in * sqrtp_cur))

# Display the new price information
print("New price:", (price_next / q96) ** 2)  # Price went DOWN
print("New sqrtP:", price_next)
print("New tick:", price_to_tick((price_next / q96) ** 2))

# Calculate EXACT amounts for the swap
amount_in = calc_amount0(liq, price_next, sqrtp_cur)   # ETH in
amount_out = calc_amount1(liq, price_next, sqrtp_cur)  # USDC out

print("ETH in:", amount_in / eth)    # How much ETH goes in
print("USDC out:", amount_out / eth) # How much USDC comes out

# ============================================
# ADDITIONAL EXAMPLE: Another USDC → ETH swap
# ============================================
# This shows what happens when we do the same swap again

print("\n" + "=" * 60)
print("REPEAT SWAP: SELLING 42 USDC AGAIN")
print("=" * 60)

amount_in = 42 * eth
price_diff = (amount_in * q96) // liq
price_next = sqrtp_cur + price_diff

print("New price:", (price_next / q96) ** 2)
print("New sqrtP:", price_next)
print("New tick:", price_to_tick((price_next / q96) ** 2))

print("\n" + "=" * 60)
print("KEY TAKEAWAYS")
print("=" * 60)
print("1. Liquidity (L) stays constant during swaps")
print("2. Selling USDC (token1) → Price goes UP → Get ETH (token0)")
print("3. Selling ETH (token0) → Price goes DOWN → Get USDC (token1)")
print("4. All calculations use √P (square root price) for precision")
print("5. Q64.96 format converts decimals to integers for smart contracts")
print("=" * 60)

amount_in = calc_amount1(liq, price_next, sqrtp_cur)
amount_out = calc_amount0(liq, price_next, sqrtp_cur)

print("USDC in:", amount_in / eth)
print("ETH out:", amount_out / eth)
# USDC in: 42.0
# ETH out: 0.008396714242162444

# Swap ETH for USDC
amount_in = 0.01337 * eth

print(f"\nSelling {amount_in/eth} ETH")

price_next = int((liq * q96 * sqrtp_cur) // (liq * q96 + amount_in * sqrtp_cur))

print("New price:", (price_next / q96) ** 2)
print("New sqrtP:", price_next)
print("New tick:", price_to_tick((price_next / q96) ** 2))

amount_in = calc_amount0(liq, price_next, sqrtp_cur)
amount_out = calc_amount1(liq, price_next, sqrtp_cur)

print("ETH in:", amount_in / eth)
print("USDC out:", amount_out / eth)
