import math
import unittest

import numpy as np
import pandas as pd

from portfolio_analysis import analyze_portfolio, prepare_close_prices


def prices():
    return pd.DataFrame({
        'AAPL': [100., 110., 99., 108.9],
        'MSFT': [100., 100., 110., 110.],
        '^GSPC': [100., 105., 99.75, 101.745],
    }, index=pd.bdate_range('2025-01-02', periods=4))


class AnalysisTests(unittest.TestCase):
    def test_known_metrics(self):
        r = analyze_portfolio(prices(), {'AAPL': 50, 'MSFT': 50})
        # Hand-calculated daily returns: +5%, 0%, +5%.
        self.assertAlmostEqual(r['Cumulative Return'], .1025)
        self.assertAlmostEqual(r['Annualized Return'], 1.1025 ** 84 - 1)
        expected_std = math.sqrt(1 / 1200)
        self.assertAlmostEqual(r['Annualized Volatility'], expected_std * math.sqrt(252))
        rf_daily = 1.04 ** (1/252) - 1
        self.assertAlmostEqual(r['Sharpe Ratio'], ((1/30 - rf_daily) * 252) / (expected_std * math.sqrt(252)))
        self.assertAlmostEqual(r['Beta'], (17/12000) / (79/30000))
        self.assertAlmostEqual(r['Maximum Drawdown'], 0)
        self.assertAlmostEqual(r['Benchmark Difference'], .1025 - .01745)
        self.assertAlmostEqual(r['Correlation Matrix'].loc['AAPL', 'MSFT'], -1)

    def test_initial_loss_is_in_drawdown(self):
        p = prices()
        p['AAPL'] = [100, 80, 90, 70]
        r = analyze_portfolio(p, {'AAPL': 100})
        self.assertAlmostEqual(r['Maximum Drawdown'], -.3)

    def test_flat_prices_have_undefined_ratios(self):
        p = prices() * 0 + 100
        r = analyze_portfolio(p, {'AAPL': 50, 'MSFT': 50})
        self.assertEqual(r['Annualized Volatility'], 0)
        self.assertTrue(math.isnan(r['Sharpe Ratio']))
        self.assertTrue(math.isnan(r['Beta']))
        self.assertEqual(r['Maximum Drawdown'], 0)

    def test_weight_order_and_rounding(self):
        p = prices()
        r = analyze_portfolio(p, {'MSFT': 50, 'AAPL': 50})
        self.assertAlmostEqual(r['Cumulative Return'], .1025)
        rounded = analyze_portfolio(p, {'AAPL': 49.99, 'MSFT': 49.99})
        self.assertAlmostEqual(rounded['Cumulative Return'], .1025)

    def test_invalid_weights(self):
        for w in [{}, {'AAPL': 90}, {'AAPL': -10, 'MSFT': 110},
                  {'AAPL': float('nan')}, {'AAPL': float('inf')}, {'AAPL': 'bad'}]:
            with self.subTest(weights=w), self.assertRaises(ValueError):
                analyze_portfolio(prices(), w)

    def test_insufficient_data(self):
        for n in [0, 1, 2]:
            with self.subTest(rows=n), self.assertRaises(ValueError):
                analyze_portfolio(prices().iloc[:n], {'AAPL': 100})

    def test_missing_internal_price_rejected(self):
        p = prices()
        p.loc[p.index[1], 'MSFT'] = np.nan
        with self.assertRaisesRegex(ValueError, 'Missing prices within'):
            analyze_portfolio(p, {'AAPL': 50, 'MSFT': 50})

    def test_all_missing_internal_row_rejected(self):
        p = prices()
        p.iloc[1] = np.nan
        with self.assertRaisesRegex(ValueError, 'Missing prices within'):
            prepare_close_prices(p, ['AAPL', 'MSFT'])

    def test_missing_edges_trimmed(self):
        p = prices()
        p.loc[p.index[0], 'MSFT'] = np.nan
        actual = prepare_close_prices(p, ['AAPL', 'MSFT'])
        pd.testing.assert_frame_equal(actual, p.iloc[1:])
        self.assertEqual(len(analyze_portfolio(p, {'MSFT': 100})['Portfolio Daily Returns']), 2)

    def test_missing_ticker_and_benchmark(self):
        for name in ['MSFT', '^GSPC']:
            with self.subTest(ticker=name), self.assertRaisesRegex(ValueError, 'Missing historical data'):
                analyze_portfolio(prices().drop(columns=name), {'MSFT': 100})
        p = prices()
        p['MSFT'] = np.nan
        with self.assertRaisesRegex(ValueError, 'Missing historical data'):
            analyze_portfolio(p, {'MSFT': 100})

    def test_bad_prices_and_dates(self):
        for value in [0, -1, float('inf'), 'bad']:
            p = prices().astype(object)
            p.iloc[1, 0] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                analyze_portfolio(p, {'AAPL': 100})
        with self.assertRaisesRegex(ValueError, 'chronological'):
            analyze_portfolio(prices().iloc[::-1], {'AAPL': 100})
        p = prices()
        p.index = [1, 1, 2, 3]
        with self.assertRaisesRegex(ValueError, 'unique'):
            analyze_portfolio(p, {'AAPL': 100})


if __name__ == '__main__':
    unittest.main()
