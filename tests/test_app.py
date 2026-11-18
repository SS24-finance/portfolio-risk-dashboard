from datetime import date, timedelta
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


def market_data():
    return pd.concat({'Close': pd.DataFrame({
        'AAPL': [100., 110., 99., 108.9],
        'MSFT': [100., 100., 110., 110.],
        '^GSPC': [100., 105., 99.75, 101.745],
    }, index=pd.bdate_range('2025-01-02', periods=4))}, axis=1)


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(APP, default_timeout=30).run()
        self.assertFalse(self.app.exception)

    def example(self):
        self.app.button(key='beginner_example').click().run()
        return self.app

    def analyze(self, data=None):
        if data is None:
            data = market_data()
        with patch('yfinance.download', return_value=data) as download:
            self.app.button[1].click().run()
        self.assertFalse(self.app.exception)
        return download

    def test_example_populates_inputs_and_resets_weights(self):
        app = self.example()
        self.assertEqual(app.text_input(key='ticker_input').value, 'AAPL, MSFT')
        self.assertEqual(app.number_input(key='weight_AAPL').value, 50)
        self.assertEqual(app.number_input(key='weight_MSFT').value, 50)
        self.assertEqual(app.date_input(key='start_date').value, date(2025, 1, 1))
        self.assertEqual(app.date_input(key='end_date').value, date(2026, 1, 1))
        app.number_input(key='weight_AAPL').set_value(70).run()
        self.example()
        self.assertEqual(app.number_input(key='weight_AAPL').value, 50)

    def test_allocations_survive_reorder_remove_and_readd(self):
        app = self.example()
        app.number_input(key='weight_AAPL').set_value(70).run()
        app.number_input(key='weight_MSFT').set_value(30).run()
        app.text_input(key='ticker_input').set_value('MSFT, AAPL, NKE').run()
        self.assertEqual(app.number_input(key='weight_AAPL').value, 70)
        self.assertEqual(app.number_input(key='weight_MSFT').value, 30)
        self.assertEqual(app.number_input(key='weight_NKE').value, 0)
        app.text_input(key='ticker_input').set_value('MSFT, NKE').run()
        app.text_input(key='ticker_input').set_value('AAPL, MSFT').run()
        self.assertEqual(app.number_input(key='weight_AAPL').value, 70)
        self.assertFalse(app.exception)

    def test_all_metrics_and_charts(self):
        app = self.example()
        download = self.analyze()
        self.assertFalse(app.error)
        self.assertEqual(len(app.metric), 8)  # Six headline + two drawdown metrics.
        self.assertEqual(len(app.get('plotly_chart')), 4)
        self.assertEqual(len(app.dataframe), 1)
        self.assertEqual(download.call_args.kwargs['start'], date(2025, 1, 1))
        self.assertEqual(download.call_args.kwargs['end'], date(2026, 1, 1))
        self.assertTrue(any('View portfolio assumptions' in e.label for e in app.expander))
        self.assertTrue(any('What do these metrics mean?' in e.label for e in app.expander))

    def test_duplicates_block_download(self):
        app = self.example()
        app.text_input(key='ticker_input').set_value('AAPL, AAPL').run()
        self.assertFalse(self.analyze().called)
        self.assertTrue(any('Duplicate' in e.value for e in app.error))

    def test_bad_allocations_block_download(self):
        app = self.example()
        app.number_input(key='weight_AAPL').set_value(10).run()
        self.assertFalse(self.analyze().called)
        self.assertTrue(any('100%' in e.value for e in app.error))

    def test_invalid_dates_block_download(self):
        app = self.example()
        app.date_input(key='start_date').set_value(date(2026, 2, 1)).run()
        self.assertFalse(self.analyze().called)
        self.assertTrue(any('before' in e.value for e in app.error))
        app.date_input(key='end_date').set_value(date.today() + timedelta(days=1)).run()
        self.assertFalse(self.analyze().called)
        self.assertTrue(any('future' in e.value for e in app.error))

    def test_missing_invalid_ticker_and_empty_download(self):
        app = self.example()
        data = market_data()
        data[('Close', 'MSFT')] = np.nan
        self.analyze(data)
        self.assertTrue(any('Missing historical data for: MSFT' in e.value for e in app.error))
        self.analyze(pd.DataFrame())
        self.assertTrue(any('No historical prices' in e.value for e in app.error))

    def test_internal_gap_and_insufficient_data(self):
        app = self.example()
        data = market_data()
        data.iloc[1, 0] = np.nan
        self.analyze(data)
        self.assertTrue(any('Missing prices within' in e.value for e in app.error))
        self.assertEqual(len(app.metric), 0)
        self.analyze(market_data().iloc[:2])
        self.assertTrue(any('Not enough' in e.value for e in app.error))

    def test_trimmed_period_warns_and_renders(self):
        app = self.example()
        data = market_data()
        data.iloc[0, 0] = np.nan
        self.analyze(data)
        self.assertTrue(any('shared period' in e.value for e in app.warning))
        self.assertEqual(len(app.get('plotly_chart')), 4)

    def test_ticker_count_and_empty_input(self):
        app = self.example()
        for symbols in ['', 'AAPL', ','.join(f'STOCK{i}' for i in range(11))]:
            app.text_input(key='ticker_input').set_value(symbols).run()
            self.assertFalse(self.analyze().called)
            self.assertTrue(any('between 2 and 10' in e.value for e in app.error))

    def test_flat_prices_render_na_without_crash(self):
        app = self.example()
        self.analyze(market_data() * 0 + 100)
        self.assertFalse(app.error)
        metrics = {m.label: m.value for m in app.metric}
        self.assertEqual(metrics['Beta'], 'N/A')
        self.assertEqual(metrics['Sharpe Ratio'], 'N/A')
        self.assertEqual(len(app.get('plotly_chart')), 4)

    def test_custom_dates_and_normalized_symbols(self):
        app = self.example()
        app.text_input(key='ticker_input').set_value(' msft , aapl ').run()
        app.date_input(key='start_date').set_value(date(2025, 2, 1)).run()
        app.date_input(key='end_date').set_value(date(2025, 3, 1)).run()
        download = self.analyze()
        self.assertEqual(download.call_args.args[0], ['MSFT', 'AAPL', '^GSPC'])
        self.assertEqual(download.call_args.kwargs['start'], date(2025, 2, 1))
        self.assertEqual(download.call_args.kwargs['end'], date(2025, 3, 1))
        self.assertFalse(download.call_args.kwargs['threads'])

    def test_network_failure_is_friendly(self):
        app = self.example()
        with patch('yfinance.download', side_effect=RuntimeError('Connection unavailable')):
            app.button[1].click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any('Unable to analyze' in e.value for e in app.error))


if __name__ == '__main__':
    unittest.main()
