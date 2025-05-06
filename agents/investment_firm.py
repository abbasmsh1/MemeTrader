from typing import Dict, List, Optional
from dataclasses import dataclass
from .trading_strategies import TradingStrategy, STRATEGIES

@dataclass
class Trader:
    """Represents a trader in the investment firm"""
    name: str
    title: str
    department: str
    strategy: TradingStrategy
    portfolio_size: float
    performance_metrics: Dict[str, float]
    risk_metrics: Dict[str, float]
    allocation_metrics: Dict[str, float]

@dataclass
class Department:
    """Represents a trading department in the investment firm"""
    name: str
    head: Trader
    traders: List[Trader]
    total_assets: float
    risk_limits: Dict[str, float]
    performance_targets: Dict[str, float]

class InvestmentFirm:
    """Represents the entire investment firm structure"""
    def __init__(self, name: str = "CryptoAlpha Capital"):
        self.name = name
        self.departments: Dict[str, Department] = {}
        self.total_assets: float = 0.0
        self.risk_limits: Dict[str, float] = {
            'max_drawdown': 0.25,
            'var_95': 0.15,
            'leverage_limit': 3.0
        }
        self._initialize_departments()

    def _initialize_departments(self):
        """Initialize the trading departments and their traders"""
        
        # Quantitative Trading Department
        quant_traders = [
            Trader(
                name="Jim Simons",
                title="Head of Quantitative Trading",
                department="Quantitative",
                strategy=STRATEGIES['quantitative'],
                portfolio_size=1000000.0,
                performance_metrics={'sharpe_ratio': 2.5, 'annual_return': 0.35},
                risk_metrics={'var_95': 0.12, 'max_drawdown': 0.15},
                allocation_metrics={'crypto': 0.4, 'defi': 0.3, 'derivatives': 0.2, 'stablecoins': 0.1}
            ),
            Trader(
                name="David Shaw",
                title="Senior Quantitative Trader",
                department="Quantitative",
                strategy=STRATEGIES['quantitative'],
                portfolio_size=750000.0,
                performance_metrics={'sharpe_ratio': 2.2, 'annual_return': 0.30},
                risk_metrics={'var_95': 0.10, 'max_drawdown': 0.12},
                allocation_metrics={'crypto': 0.45, 'defi': 0.25, 'derivatives': 0.2, 'stablecoins': 0.1}
            )
        ]
        
        self.departments['Quantitative'] = Department(
            name="Quantitative Trading",
            head=quant_traders[0],
            traders=quant_traders,
            total_assets=sum(t.portfolio_size for t in quant_traders),
            risk_limits={'max_drawdown': 0.15, 'var_95': 0.12},
            performance_targets={'sharpe_ratio': 2.0, 'annual_return': 0.30}
        )

        # Fundamental Trading Department
        fundamental_traders = [
            Trader(
                name="Warren Buffett",
                title="Head of Fundamental Trading",
                department="Fundamental",
                strategy=STRATEGIES['fundamental'],
                portfolio_size=1500000.0,
                performance_metrics={'sharpe_ratio': 1.8, 'annual_return': 0.25},
                risk_metrics={'var_95': 0.08, 'max_drawdown': 0.10},
                allocation_metrics={'crypto': 0.6, 'defi': 0.2, 'stablecoins': 0.2}
            ),
            Trader(
                name="Charlie Munger",
                title="Senior Fundamental Analyst",
                department="Fundamental",
                strategy=STRATEGIES['fundamental'],
                portfolio_size=1000000.0,
                performance_metrics={'sharpe_ratio': 1.7, 'annual_return': 0.22},
                risk_metrics={'var_95': 0.07, 'max_drawdown': 0.09},
                allocation_metrics={'crypto': 0.65, 'defi': 0.15, 'stablecoins': 0.2}
            )
        ]
        
        self.departments['Fundamental'] = Department(
            name="Fundamental Trading",
            head=fundamental_traders[0],
            traders=fundamental_traders,
            total_assets=sum(t.portfolio_size for t in fundamental_traders),
            risk_limits={'max_drawdown': 0.10, 'var_95': 0.08},
            performance_targets={'sharpe_ratio': 1.5, 'annual_return': 0.20}
        )

        # Momentum Trading Department
        momentum_traders = [
            Trader(
                name="Paul Tudor Jones",
                title="Head of Momentum Trading",
                department="Momentum",
                strategy=STRATEGIES['momentum'],
                portfolio_size=1200000.0,
                performance_metrics={'sharpe_ratio': 2.0, 'annual_return': 0.28},
                risk_metrics={'var_95': 0.11, 'max_drawdown': 0.13},
                allocation_metrics={'crypto': 0.5, 'defi': 0.3, 'stablecoins': 0.2}
            ),
            Trader(
                name="Stanley Druckenmiller",
                title="Senior Momentum Trader",
                department="Momentum",
                strategy=STRATEGIES['momentum'],
                portfolio_size=800000.0,
                performance_metrics={'sharpe_ratio': 1.9, 'annual_return': 0.25},
                risk_metrics={'var_95': 0.10, 'max_drawdown': 0.12},
                allocation_metrics={'crypto': 0.55, 'defi': 0.25, 'stablecoins': 0.2}
            )
        ]
        
        self.departments['Momentum'] = Department(
            name="Momentum Trading",
            head=momentum_traders[0],
            traders=momentum_traders,
            total_assets=sum(t.portfolio_size for t in momentum_traders),
            risk_limits={'max_drawdown': 0.12, 'var_95': 0.10},
            performance_targets={'sharpe_ratio': 1.8, 'annual_return': 0.25}
        )

        # Arbitrage Trading Department
        arbitrage_traders = [
            Trader(
                name="Ken Griffin",
                title="Head of Arbitrage Trading",
                department="Arbitrage",
                strategy=STRATEGIES['arbitrage'],
                portfolio_size=900000.0,
                performance_metrics={'sharpe_ratio': 2.2, 'annual_return': 0.20},
                risk_metrics={'var_95': 0.06, 'max_drawdown': 0.08},
                allocation_metrics={'crypto': 0.7, 'stablecoins': 0.3}
            ),
            Trader(
                name="Ray Dalio",
                title="Senior Arbitrage Trader",
                department="Arbitrage",
                strategy=STRATEGIES['arbitrage'],
                portfolio_size=600000.0,
                performance_metrics={'sharpe_ratio': 2.1, 'annual_return': 0.18},
                risk_metrics={'var_95': 0.05, 'max_drawdown': 0.07},
                allocation_metrics={'crypto': 0.75, 'stablecoins': 0.25}
            )
        ]
        
        self.departments['Arbitrage'] = Department(
            name="Arbitrage Trading",
            head=arbitrage_traders[0],
            traders=arbitrage_traders,
            total_assets=sum(t.portfolio_size for t in arbitrage_traders),
            risk_limits={'max_drawdown': 0.08, 'var_95': 0.06},
            performance_targets={'sharpe_ratio': 2.0, 'annual_return': 0.15}
        )

        # Venture Capital Department
        venture_traders = [
            Trader(
                name="Peter Thiel",
                title="Head of Venture Capital",
                department="Venture",
                strategy=STRATEGIES['venture'],
                portfolio_size=2000000.0,
                performance_metrics={'sharpe_ratio': 1.5, 'annual_return': 0.40},
                risk_metrics={'var_95': 0.20, 'max_drawdown': 0.25},
                allocation_metrics={'crypto': 0.3, 'defi': 0.4, 'gaming': 0.2, 'stablecoins': 0.1}
            ),
            Trader(
                name="Marc Andreessen",
                title="Senior Venture Partner",
                department="Venture",
                strategy=STRATEGIES['venture'],
                portfolio_size=1500000.0,
                performance_metrics={'sharpe_ratio': 1.4, 'annual_return': 0.35},
                risk_metrics={'var_95': 0.18, 'max_drawdown': 0.22},
                allocation_metrics={'crypto': 0.25, 'defi': 0.45, 'gaming': 0.2, 'stablecoins': 0.1}
            )
        ]
        
        self.departments['Venture'] = Department(
            name="Venture Capital",
            head=venture_traders[0],
            traders=venture_traders,
            total_assets=sum(t.portfolio_size for t in venture_traders),
            risk_limits={'max_drawdown': 0.25, 'var_95': 0.20},
            performance_targets={'sharpe_ratio': 1.3, 'annual_return': 0.35}
        )

        # Calculate total assets
        self.total_assets = sum(dept.total_assets for dept in self.departments.values())

    def get_department(self, name: str) -> Optional[Department]:
        """Get a department by name"""
        return self.departments.get(name)

    def get_trader(self, name: str) -> Optional[Trader]:
        """Get a trader by name"""
        for dept in self.departments.values():
            for trader in dept.traders:
                if trader.name == name:
                    return trader
        return None

    def get_department_performance(self, department_name: str) -> Dict[str, float]:
        """Get performance metrics for a department"""
        dept = self.get_department(department_name)
        if not dept:
            return {}
        
        return {
            'total_assets': dept.total_assets,
            'avg_sharpe_ratio': sum(t.performance_metrics['sharpe_ratio'] for t in dept.traders) / len(dept.traders),
            'avg_annual_return': sum(t.performance_metrics['annual_return'] for t in dept.traders) / len(dept.traders),
            'avg_var_95': sum(t.risk_metrics['var_95'] for t in dept.traders) / len(dept.traders),
            'avg_max_drawdown': sum(t.risk_metrics['max_drawdown'] for t in dept.traders) / len(dept.traders)
        }

    def get_firm_performance(self) -> Dict[str, float]:
        """Get overall firm performance metrics"""
        total_sharpe = 0
        total_return = 0
        total_var = 0
        total_drawdown = 0
        trader_count = 0

        for dept in self.departments.values():
            for trader in dept.traders:
                total_sharpe += trader.performance_metrics['sharpe_ratio']
                total_return += trader.performance_metrics['annual_return']
                total_var += trader.risk_metrics['var_95']
                total_drawdown += trader.risk_metrics['max_drawdown']
                trader_count += 1

        return {
            'total_assets': self.total_assets,
            'avg_sharpe_ratio': total_sharpe / trader_count,
            'avg_annual_return': total_return / trader_count,
            'avg_var_95': total_var / trader_count,
            'avg_max_drawdown': total_drawdown / trader_count
        } 