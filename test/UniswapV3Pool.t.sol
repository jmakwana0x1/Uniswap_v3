//SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {UniswapV3Pool} from "../src/UniswapV3Pool.sol";
import {ERC20Mintable} from "./ERC20Mintable.sol";

contract UniswapV3PoolTest is Test{

    ERC20Mintable token0;
    ERC20Mintable token1;
    UniswapV3Pool pool;
    // Flag to control whether we transfer tokens in callback
    bool shouldTransferInCallback;

    struct TestCaseParams {
        uint256 wethBalance;           // How much WETH test contract starts with
        uint256 usdcBalance;           // How much USDC test contract starts with
        int24 currentTick;             // Current tick for the pool
        int24 lowerTick;               // Lower bound of liquidity range
        int24 upperTick;               // Upper bound of liquidity range
        uint128 liquidity;             // Amount of liquidity to provide
        uint160 currentSqrtP;          // Current √P in Q64.96 format
        bool shouldTransferInCallback; // Should we send tokens in callback?
        bool mintLiqudity;            // Should we actually mint liquidity?
    }
    function setUp()public{
        token0 = new ERC20Mintable("Ether","ETH",18);
        token1 = new ERC20Mintable("USD Coin","USDC",18);
    }

    function testExample()public{
        assertTrue(true);
    }

    function testMintSuccess() public {
        // Define all the parameters for this test case
        TestCaseParams memory params = TestCaseParams({
        wethBalance: 1 ether,
        usdcBalance: 5000 ether,
        currentTick: 85176,
        lowerTick: 84222,
        upperTick: 86129,
        liquidity: 1517882343751509868544,
        currentSqrtP: 5602277097478614198912276234240,
        shouldTransferInCallback: true,
        mintLiqudity: true
    });

        // Setup the pool and mint liquidity
        // Returns how many tokens were actually deposited
        (uint256 poolBalance0, uint256 poolBalance1) = setupTestCase(params);

        // ============================================
        // ASSERTION 1: Check token amounts deposited
        // ============================================
        uint256 expectedAmount0 = 0.998976618347425280 ether;  // Expected ETH
        uint256 expectedAmount1 = 5000 ether;                   // Expected USDC
        
        assertEq(
            poolBalance0,
            expectedAmount0,
            "incorrect token0 deposited amount"
        );
        assertEq(
            poolBalance1,
            expectedAmount1,
            "incorrect token1 deposited amount"
        );

        // ============================================
        // ASSERTION 2: Check tokens were transferred to pool
        // ============================================
        assertEq(token0.balanceOf(address(pool)), expectedAmount0);
        assertEq(token1.balanceOf(address(pool)), expectedAmount1);

        // ============================================
        // ASSERTION 3: Check position was created correctly
        // ============================================
        // Calculate the position key (same hash the pool uses)
        bytes32 positionKey = keccak256(
            abi.encodePacked(
                address(this),      // Owner = this test contract
                params.lowerTick,   // Lower tick
                params.upperTick    // Upper tick
            )
        );
        
        // Get the position's liquidity from the pool
        uint128 posLiquidity = pool.positions(positionKey);
        
        // Check it matches what we provided
        assertEq(posLiquidity, params.liquidity);

        // ============================================
        // ASSERTION 4: Check lower tick was initialized
        // ============================================
        (bool tickInitialized, uint128 tickLiquidity) = pool.ticks(
            params.lowerTick
        );
        assertTrue(tickInitialized);
        assertEq(tickLiquidity, params.liquidity);

        // ============================================
        // ASSERTION 5: Check upper tick was initialized
        // ============================================
        (tickInitialized, tickLiquidity) = pool.ticks(params.upperTick);
        assertTrue(tickInitialized);
        assertEq(tickLiquidity, params.liquidity);

        // ============================================
        // ASSERTION 6: Check pool's √P and tick
        // ============================================
        (uint160 sqrtPriceX96, int24 tick) = pool.slot0();
        assertEq(
            sqrtPriceX96,
            5602277097478614198912276234240,
            "invalid current sqrtP"
        );
        assertEq(tick, 85176, "invalid current tick");
        
        // ============================================
        // ASSERTION 7: Check pool's total liquidity
        // ============================================
        assertEq(
            pool.liquidity(),
            1517882343751509868544,
            "invalid current liquidity"
        );
    }

    // ============================================
    // HELPER: Setup Test Case
    // ============================================
    // This function:
    // 1. Mints tokens to the test contract
    // 2. Deploys a new pool
    // 3. Optionally mints liquidity
    function setupTestCase(TestCaseParams memory params)
    internal
    returns (uint256 poolBalance0, uint256 poolBalance1)
{
    token0.mint(address(this), params.wethBalance);
    token1.mint(address(this), params.usdcBalance);

    pool = new UniswapV3Pool(
        address(token0),
        address(token1),
        params.currentSqrtP,
        params.currentTick
    );

    shouldTransferInCallback = params.shouldTransferInCallback;
    if (params.mintLiqudity) {
        (poolBalance0, poolBalance1) = pool.mint(
            address(this),
            params.lowerTick,
            params.upperTick,
            params.liquidity,
            ""
        );
    }

}

function uniswapV3MintCallback(uint256 amount0, uint256 amount1,bytes calldata data) public {
    if (shouldTransferInCallback) {
        token0.transfer(msg.sender, amount0);
        token1.transfer(msg.sender, amount1);
    }
}

    function testSwapBuyEth() public {
    TestCaseParams memory params = TestCaseParams({
        wethBalance: 1 ether,
        usdcBalance: 5000 ether,
        currentTick: 85176,
        lowerTick: 84222,
        upperTick: 86129,
        liquidity: 1517882343751509868544,
        currentSqrtP: 5602277097478614198912276234240,
        shouldTransferInCallback: true,
        mintLiqudity: true
    });

    (uint256 poolBalance0, uint256 poolBalance1) = setupTestCase(params);
    uint256 userBalance0Before = token0.balanceOf(address(this)); 
    token1.mint(address(this), 42 ether);
(int256 amount0Delta, int256 amount1Delta) = pool.swap(address(this));
assertEq(
    token0.balanceOf(address(this)),
    uint256(int256(userBalance0Before) - amount0Delta),
    "invalid user ETH balance"
);
assertEq(
    token1.balanceOf(address(this)),
    0,
    "invalid user USDC balance"
);
assertEq(
    token0.balanceOf(address(pool)),
    uint256(int256(poolBalance0) + amount0Delta),
    "invalid pool ETH balance"
);
assertEq(
    token1.balanceOf(address(pool)),
    uint256(int256(poolBalance1) + amount1Delta),
    "invalid pool USDC balance"
);
(uint160 sqrtPriceX96, int24 tick) = pool.slot0();
assertEq(
    sqrtPriceX96,
    5604469350942327889444743441197,
    "invalid current sqrtP"
);
assertEq(tick, 85184, "invalid current tick");
assertEq(
    pool.liquidity(),
    1517882343751509868544,
    "invalid current liquidity"
);

    }
function uniswapV3SwapCallback(int256 amount0, int256 amount1) public {
    if (amount0 > 0) {
        token0.transfer(msg.sender, uint256(amount0));
    }

    if (amount1 > 0) {
        token1.transfer(msg.sender, uint256(amount1));
    }
}


    
}