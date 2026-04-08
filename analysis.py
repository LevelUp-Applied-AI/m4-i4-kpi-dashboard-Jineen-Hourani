"""Integration 4 — KPI Dashboard: Amman Digital Market Analytics

Extract data from PostgreSQL, compute KPIs, run statistical tests,
and create visualizations for the executive summary.

Usage:
    python analysis.py
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sqlalchemy import create_engine


def connect_db():
    """Create a SQLAlchemy engine connected to the amman_market database.

    Returns:
        engine: SQLAlchemy engine instance

    Notes:
        Use DATABASE_URL environment variable if set, otherwise default to:
        postgresql://postgres:postgres@localhost:5432/amman_market
    """
    # TODO: Create and return a SQLAlchemy engine using DATABASE_URL or a default
    
    engine = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/amman_market")
    return engine

def extract_data(engine):
    """Extract all required tables from the database into DataFrames.

    Args:
        engine: SQLAlchemy engine connected to amman_market

    Returns:
        dict: mapping of table names to DataFrames
              (e.g., {"customers": df, "products": df, "orders": df, "order_items": df})
    """
    # TODO: Query each table and return a dictionary of DataFrames
    
    tables = ["customers", "products", "orders", "order_items"]
    data_dict = {}

    for table in tables:
        data_dict[table] = pd.read_sql_table(table, engine)
        print(f"Extracted {len(data_dict[table])} rows from {table}")
        
    data_dict['orders'] = data_dict['orders'][data_dict['orders']['status'] != 'cancelled']
    
    data_dict['order_items'] = data_dict['order_items'][data_dict['order_items']['quantity'] <= 100]

    data_dict['customers']['city'] = data_dict['customers']['city'].fillna('Unknown')

    return data_dict

def prepare_master_df(data_dict):
    orders = data_dict['orders']
    items = data_dict['order_items']
    products = data_dict['products']
    customers = data_dict['customers']
 
    df = orders.merge(items, on='order_id')\
               .merge(products, on='product_id')\
               .merge(customers, on='customer_id')


    df['line_total'] = df['quantity'] * df['unit_price'].astype(float)
    df['order_date'] = pd.to_datetime(df['order_date'])
    
    return df




def compute_kpis(df):
    """Compute the 5 KPIs defined in kpi_framework.md.

    Args:
        data_dict: dict of DataFrames from extract_data()

    Returns:
        dict: mapping of KPI names to their computed values (or DataFrames
              for time-series / cohort KPIs)

    Notes:
        At least 2 KPIs should be time-based and 1 should be cohort-based.
    """
    # TODO: Join tables as needed, then compute each KPI from your framework
    # TODO: Return results as a dictionary for use in visualizations
   
    results = {}

    # Ensure order_date is in datetime format for time-based analysis
    df['order_date'] = pd.to_datetime(df['order_date'])

    # KPI 1: Monthly Total Revenue (Time-based)
    # Using 'ME' instead of 'M' to avoid Pandas 2.0+ deprecation errors
    results['monthly_revenue'] = df.set_index('order_date').resample('ME')['line_total'].sum()

    # KPI 2: Monthly Order Volume (Time-based)
    # Using 'ME' for monthly frequency grouping
    results['monthly_orders'] = df.set_index('order_date').resample('ME')['order_id'].nunique()

    # KPI 3: Revenue by City (Cohort-based)
    # Grouping by customer city and summing total revenue
    results['revenue_by_city'] = df.groupby('city')['line_total'].sum().sort_values(ascending=False)

    # KPI 4: Average Order Value (AOV)
    # Total Revenue divided by Total Unique Orders
    total_revenue = df['line_total'].sum()
    total_orders = df['order_id'].nunique()
    results['avg_order_value'] = total_revenue / total_orders if total_orders > 0 else 0

    # KPI 5: Top Selling Categories
    # Grouping by product category and sorting by revenue
    results['top_categories'] = df.groupby('category')['line_total'].sum().sort_values(ascending=False)

    return results


def run_statistical_tests(df):
    """Run hypothesis tests to validate patterns in the data.

    Args:
        data_dict: dict of DataFrames from extract_data()

    Returns:
        dict: mapping of test names to results (test statistic, p-value,
              interpretation)

    Notes:
        Run at least one test. Consider:
        - Does average order value differ across product categories?
        - Is there a significant trend in monthly revenue?
        - Do customer cities differ in purchasing behavior?
    """
    # TODO: Select and run appropriate statistical tests
    # TODO: Interpret results (reject or fail to reject the null hypothesis)
 
    """
    Perform ANOVA test and calculate Effect Size (Eta-squared) 
    to see if spending differs by product category.
    """
    results = {}

    # 1. Prepare groups for ANOVA
    categories = df['category'].unique()
    group_data = [df[df['category'] == cat]['line_total'] for cat in categories]

    # 2. Perform One-Way ANOVA
    f_stat, p_val = stats.f_oneway(*group_data)

    # 3. Calculate Eta-squared (Effect Size)
    overall_mean = df['line_total'].mean()
    ss_total = ((df['line_total'] - overall_mean)**2).sum()
    ss_between = sum([len(g) * (g.mean() - overall_mean)**2 for g in group_data])
    eta_sq = ss_between / ss_total if ss_total != 0 else 0

    # 4. Define the Interpretation based on p-value
    if p_val < 0.05:
        interpretation = "Significant difference found! Category affects spending."
    else:
        interpretation = "No significant difference. Spending is similar across categories."

    # 5. Define Effect Size Magnitude
    if eta_sq < 0.06:
        effect_label = "Small"
    elif eta_sq < 0.14:
        effect_label = "Medium"
    else:
        effect_label = "Large"

    # 6. Store everything in the results dictionary
    results['anova_category_test'] = {
        'statistic': round(f_stat, 3),
        'p_value': p_val, # Keeping raw p-value for scientific accuracy
        'eta_squared': round(eta_sq, 3),
        'effect_size_label': effect_label,
        'interpretation': interpretation
    }

    return results

def create_visualizations(kpi_results, stat_results):
    """Create publication-quality charts for all 5 KPIs.

    Args:
        kpi_results: dict from compute_kpis()
        stat_results: dict from run_statistical_tests()

    Returns:
        None

    Side effects:
        Saves at least 5 PNG files to the output/ directory.
        Each chart should have a descriptive title stating the finding,
        proper axis labels, and annotations where appropriate.
    """
    # TODO: Create one visualization per KPI, saved to output/
    # TODO: Use appropriate chart types (bar, line, scatter, heatmap, etc.)
    # TODO: Ensure titles state the insight, not just the data

    # Set the visual style
    sns.set_theme(style="whitegrid")

    # 1. KPI 1: Monthly Revenue (Line Chart)
    plt.figure(figsize=(10, 6))
    kpi_results['monthly_revenue'].plot(kind='line', marker='o', color='b', linewidth=2)
    plt.title('Monthly Revenue Trend: Notable Growth in Mid-2025', fontsize=14)
    plt.xlabel('Month')
    plt.ylabel('Total Revenue (JOD)')
    plt.savefig('output/kpi1_monthly_revenue.png')
    plt.close()

    # 2. KPI 2: Monthly Orders (Bar Chart)
    plt.figure(figsize=(10, 6))
    kpi_results['monthly_orders'].plot(kind='bar', color='skyblue')
    plt.title('Monthly Order Volume: Sharp Spike in June 2025', fontsize=14)
    plt.xlabel('Month')
    plt.ylabel('Number of Orders')
    plt.xticks(rotation=45)
    plt.savefig('output/kpi2_monthly_orders.png')
    plt.close()

    # 3. KPI 3: Revenue by City (Horizontal Bar Chart)
    plt.figure(figsize=(10, 6))
    kpi_results['revenue_by_city'].plot(kind='barh', color='salmon')
    plt.title('Revenue by City: Amman Dominates the Market', fontsize=14)
    plt.xlabel('Total Revenue (JOD)')
    plt.ylabel('City')
    plt.savefig('output/kpi3_revenue_by_city.png')
    plt.close()

    # 4. KPI 5: Top Categories (Pie Chart)
    plt.figure(figsize=(8, 8))
    kpi_results['top_categories'].plot(kind='pie', autopct='%1.1f%%', startangle=140)
    plt.title('Revenue Distribution by Category', fontsize=14)
    plt.ylabel('') # Remove y-label for pie charts
    plt.savefig('output/kpi5_category_share.png')
    plt.close()

    # 5. Statistical Visualization: ANOVA (Box Plot)
    # Note: This requires the master_df, so we might pass it or use a simplified summary
    # For now, let's create a summary of the Stat Results as a text-based image or Bar
    plt.figure(figsize=(8, 4))
    plt.text(0.1, 0.5, f"ANOVA P-Value: {stat_results['anova_category_test']['p_value']:.2e}\n"
                     f"Effect Size (Eta Sq): {stat_results['anova_category_test']['eta_squared']}\n"
                     f"Result: {stat_results['anova_category_test']['interpretation']}", 
             fontsize=12, bbox=dict(facecolor='yellow', alpha=0.5))
    plt.axis('off')
    plt.title('Statistical Test Summary (ANOVA)', fontsize=14)
    plt.savefig('output/statistical_test_summary.png')
    plt.close()

    print("Visualizations saved successfully in the 'output/' folder.")


def main():
    """Orchestrate the full analysis pipeline."""
    os.makedirs("output", exist_ok=True)

    # TODO: Connect to the database
    engine = connect_db()
    # TODO: Extract data
    data_dict = extract_data(engine)
    df = prepare_master_df(data_dict)
    # TODO: Compute KPIs
    kpi_results = compute_kpis(df)
    '''   
    print("\n" + "="*30)
    print("KPI 1: Monthly Revenue")
    print(kpi_results['monthly_revenue'])
    
    print("\n" + "="*30)
    print("KPI 2: Monthly Orders")
    print(kpi_results['monthly_orders'])
    
    print("\n" + "="*30)
    print("KPI 3: Revenue by City")
    print(kpi_results['revenue_by_city'])
    
    print("\n" + "="*30)
    print(f"KPI 4: Average Order Value (AOV): {kpi_results['avg_order_value']:.2f} JOD")
    
    print("\n" + "="*30)
    print("KPI 5: Top Selling Categories")
    print(kpi_results['top_categories'])
    '''
    # TODO: Run statistical tests
    stat_results = run_statistical_tests(df)
    #print("\n--- statistical tests results ---\n" , stat_results)
    # TODO: Create visualizations
    create_visualizations(kpi_results, stat_results)
    # TODO: Print a summary of KPI values and test results
    # --- Final Summary Report ---
    print("\n" + "="*40)
    print("      EXECUTIVE SUMMARY REPORT")
    print("="*40)
    print(f"Total Revenue Managed: {kpi_results['monthly_revenue'].sum():.2f} JOD")
    print(f"Average Customer Spend (AOV): {kpi_results['avg_order_value']:.2f} JOD")
    print(f"Top Performing City: {kpi_results['revenue_by_city'].idxmax()}")
    print(f"Statistical Significance: {'YES' if stat_results['anova_category_test']['p_value'] < 0.05 else 'NO'}")
    print(f"Effect Size: {stat_results['anova_category_test']['effect_size_label']}")
    print("="*40)
    print("Analysis complete. All charts saved in /output folder.")

if __name__ == "__main__":
    main()
