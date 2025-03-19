# portfolio_adapter.py

import builtins
import pandas as pd
import plotly.graph_objects as go

import utils.backtest_backend # imports backtester dynamically
BACKTEST_BACKEND = getattr(builtins, "BACKTEST_BACKEND", "vectorbt")
import abstractbt as vbt


class BacktestAdapter:
    """
    A unified adapter for portfolio objects that hides API differences between 
    vectorbt and vectorbtpro (and future backtesting libraries).
    """

    def __init__(self, pf):
        self._pf = pf

    @property
    def value(self):
        # vectorbtpro uses a property; vectorbt a callable
        if BACKTEST_BACKEND == "vectorbt":
            return self._pf.value()
        return self._pf.value

    @property
    def cumulative_returns(self):
        if BACKTEST_BACKEND == "vectorbt":
            return self._pf.cumulative_returns()
        return self._pf.cumulative_returns

    @property
    def returns(self):
        if BACKTEST_BACKEND == "vectorbt":
            return self._pf.returns()
        return self._pf.returns

    @property
    def sharpe_ratio(self):
        if BACKTEST_BACKEND == "vectorbt":
            return self._pf.sharpe_ratio()
        return self._pf.get_sharpe_ratio()

    @property
    def sortino_ratio(self):
        if BACKTEST_BACKEND == "vectorbt":
            return self._pf.sortino_ratio()
        return self._pf.get_sortino_ratio()

    @property
    def benchmark_cumulative_returns(self):
        if BACKTEST_BACKEND == "vectorbt":
            return self._pf.cumulative_returns()
        return self._pf.benchmark_cumulative_returns

    @property
    def trade_history(self):
        if BACKTEST_BACKEND == "vectorbt":
            raise NotImplementedError('This method is not implemented in vectorbt')
        return self._pf.trade_history
    
    @property
    def total_return(self):
        if BACKTEST_BACKEND == "vectorbt":
            return self._pf.total_return()
        return self._pf.total_return
    
    @property
    def max_drawdown(self):
        if BACKTEST_BACKEND == "vectorbt":
            return self._pf.max_drawdown()
        return self._pf.max_drawdown

    def plot_expanding_mfe_returns(self):
        if BACKTEST_BACKEND == "vectorbt":
            raise NotImplementedError('This method is not implemented in vectorbt')
        return self._pf.trades.plot_expanding_mfe_returns()

    def plot_expanding_mae_returns(self):
        if BACKTEST_BACKEND == "vectorbt":
            raise NotImplementedError('This method is not implemented in vectorbt')
        return self._pf.trades.plot_expanding_mae_returns()

    @classmethod
    def from_signals(cls, close, open, entries, exits, direction, init_cash,
                     cash_sharing, size, size_type, fees, slippage, allow_partial,
                     freq, sim_start=None, sim_end=None):
        """
        Factory method that adapts differences in the from_signals API.
        
        For vectorbtpro:
            - Pass all parameters including `open`, `sim_start`, `sim_end`
            - size_type remains a string (e.g. "valuepercent")
        
        For vectorbt:
            - Omit `open`, `sim_start`, and `sim_end`
            - Translate size_type "valuepercent" into numeric code 2.
        """
        if BACKTEST_BACKEND == "vectorbtbro":
            pf = vbt.Portfolio.from_signals(
                close=close,
                open=open,
                entries=entries,
                exits=exits,
                direction=direction,
                init_cash=init_cash,
                cash_sharing=cash_sharing,
                size=size,
                size_type=size_type,
                fees=fees,
                slippage=slippage,
                allow_partial=allow_partial,
                freq=freq,
                sim_start=sim_start,
                sim_end=sim_end,
            )
        elif BACKTEST_BACKEND == "vectorbt":
            # Adjust parameters:
            # - Omit open, sim_start, sim_end.
            # - Convert size_type from string to numeric if needed.
            size_type_converted = 2 if isinstance(size_type, str) and size_type.lower() == "valuepercent" else size_type
            pf = vbt.Portfolio.from_signals(
                close=close,
                entries=entries,
                exits=exits,
                direction=direction,
                init_cash=init_cash,
                cash_sharing=cash_sharing,
                size=size,
                size_type=size_type_converted,
                fees=fees,
                slippage=slippage,
                allow_partial=allow_partial,
                freq=freq
            )
        else:
            raise NotImplementedError(f"Backend '{BACKTEST_BACKEND}' not supported.")
        return cls(pf)
    
    def __getattr__(self, name):
        """
        Delegate attribute access to the underlying portfolio object.
        This way, if an attribute isn't defined on the adapter,
        it will try to fetch it from self._pf.
        """
        return getattr(self._pf, name)
