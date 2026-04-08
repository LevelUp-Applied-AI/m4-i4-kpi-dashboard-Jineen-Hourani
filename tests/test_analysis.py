"""Tests for the KPI dashboard analysis.

Write at least 3 tests:
1. test_extraction_returns_dataframes — extract_data returns a dict of DataFrames
2. test_kpi_computation_returns_expected_keys — compute_kpis returns a dict with your 5 KPI names
3. test_statistical_test_returns_pvalue — run_statistical_tests returns results with p-values
"""

import pytest
import numpy as np
import pandas as pd
from analysis import connect_db, extract_data, prepare_master_df, compute_kpis, run_statistical_tests

def test_extraction_returns_dataframes():
    """Connect to the database, extract data, and verify the result is a dict of DataFrames."""
    # TODO: Call connect_db and extract_data, then assert the result is a dict
    #       with DataFrame values for each expected table
    engine = connect_db()
    data_dict = extract_data(engine)
    
    # Check if result is a dictionary
    assert isinstance(data_dict, dict)
    
    # Check if expected tables exist and are pandas DataFrames
    expected_tables = ['customers', 'products', 'orders', 'order_items']
    for table in expected_tables:
        assert table in data_dict
        assert isinstance(data_dict[table], pd.DataFrame)


def test_kpi_computation_returns_expected_keys():
    """Compute KPIs and verify the result contains all expected KPI names."""
    # TODO: Extract data, call compute_kpis, then assert the returned dict
    #       contains the keys matching your 5 KPI names
    engine = connect_db()
    data_dict = extract_data(engine)
    master_df = prepare_master_df(data_dict)
    kpi_results = compute_kpis(master_df)
    
    # Assert the dictionary contains our 5 KPI keys
    expected_keys = [
        'monthly_revenue', 
        'monthly_orders', 
        'revenue_by_city', 
        'avg_order_value', 
        'top_categories'
    ]
    for key in expected_keys:
        assert key in kpi_results, f"KPI {key} is missing from results"



def test_statistical_test_returns_pvalue():
    """Run statistical tests and verify results include p-values."""
    # TODO: Extract data, call run_statistical_tests, then assert at least
    #       one result contains a numeric p-value between 0 and 1
    engine = connect_db()
    data_dict = extract_data(engine)
    master_df = prepare_master_df(data_dict)
    stat_results = run_statistical_tests(master_df)
    
    # Assert that ANOVA results exist
    assert 'anova_category_test' in stat_results
    
    # Verify p_value is a number and within valid probability range (0 to 1)
    p_val = stat_results['anova_category_test']['p_value']
    assert isinstance(p_val, (float, int, np.number))
    assert 0 <= p_val <= 1
 


 

