"""
Privacy-enhancing technology workflows extracted from the notebook.
"""
import io
import base64
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
import random
import time
import numpy as np
import pandas as pd
import polars as pl
import opendp.prelude as dp
import anjana.anonymity
from tqdm import tqdm
import pailliers
from typing import List, Dict, Any, Tuple


def generate_sample_data(num_events: int = 5000, num_conversions: int = 1000, seed: int = 123):
    """Generate sample engagement events and conversion data."""
    import faker

    random.seed(seed)
    faker.Faker.seed(seed)
    fake = faker.Faker()

    # Generate email pool
    emails = [fake.email() for _ in range(10000)]
    emails = random.sample(emails, 10000)

    campaigns = ['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Purple']
    regions = ['NA', 'LATAM', 'EMEA', 'APAC', 'ROW']

    # Generate events
    events = [
        [
            random.randint(1, 1),
            emails[i],
            'click',
            random.choice(campaigns),
            random.choice(regions),
            random.choice([False, True])
        ]
        for i in range(num_events)
    ]

    # Generate conversions
    emails_sample = random.sample(emails, num_conversions)
    types = ['Purchase', 'Subscription']
    conversions = [
        [
            random.randint(1, 1),
            emails_sample[i],
            random.choice(types)
        ]
        for i in range(len(emails_sample))
    ]

    return events, conversions, campaigns


def join_events_conversions(events, conversions):
    """Join events with conversions on email address."""
    joined = [
        [
            spaceid_e,
            type_e,
            campaign_e,
            region_e,
            opt_e,
            type_c
        ]
        for (spaceid_e, key_e, type_e, campaign_e, region_e, opt_e) in events
        for (spaceid_c, key_c, type_c) in conversions
        if key_e == key_c
    ]
    return joined


def aggregate_conversions(joined_data, campaigns):
    """Aggregate conversion counts by campaign."""
    aggregate = [
        [
            campaign,
            sum([
                1
                for (_, _, campaign_, _, _, _) in joined_data
                if campaign == campaign_
            ])
        ]
        for campaign in campaigns
    ]
    return aggregate


def k_anonymity_workflow(events, conversions, k: int = 10, supp_level: int = 50):
    """
    Apply k-anonymity to the joined dataset.

    Args:
        events: List of engagement events
        conversions: List of conversion events
        k: k-anonymity parameter
        supp_level: Suppression level

    Returns:
        DataFrame with k-anonymous data
    """
    campaigns = ['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Purple']

    # Join data
    join_ka = join_events_conversions(events, conversions)

    # Add age and sex columns for more interesting example
    data = pd.DataFrame([
        row[2:] + [
            random.randint(18, 88),
            random.choice(['F', 'M'])
        ]
        for row in join_ka
    ], columns=[
        'event_properties.promotion_name',
        'user_data.address.region',
        'user_data.opt_out',
        'event_type',
        'user_data.age',
        'user_data.sex'
    ])

    # Define range function
    def range_from(age):
        for i in range(0, 100, 10):
            if i <= int(age) < i + 10:
                return '[' + str(i) + ', ' + str(i + 10) + ')'

    # Define hierarchies
    hierarchies = {
        'user_data.age': {
            0: data['user_data.age'].values,
            1: [range_from(v) for v in data['user_data.age'].values]
        },
        'user_data.sex': {
            0: data['user_data.sex'].values,
            1: np.array(["*"] * len(data["user_data.sex"].values))
        },
        'user_data.address.region': {
            0: data['user_data.address.region'].values,
            1: np.array(['*'] * len(data['user_data.sex'].values))
        }
    }

    # Apply k-anonymity
    result = anjana.anonymity.k_anonymity(
        data,
        ['event_properties.promotion_name'],  # Identifiers
        ['user_data.age', 'user_data.sex', 'user_data.address.region'],  # Quasi-identifiers
        k,
        supp_level,
        hierarchies
    )

    return result.to_dict('records')


def differential_privacy_workflow(events, conversions, epsilon: float = 1.0, split_evenly_over: int = 6):
    """
    Apply differential privacy to conversion counts.

    Args:
        events: List of engagement events
        conversions: List of conversion events
        epsilon: Privacy loss parameter
        split_evenly_over: Number of queries to split privacy budget over

    Returns:
        Dictionary with non-DP and DP counts for each campaign
    """
    dp.enable_features("contrib")

    campaigns = ['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Purple']
    join_dp = join_events_conversions(events, conversions)

    comparison = []

    for campaign in campaigns:
        # Filter for this campaign
        filtered = [
            1
            for [spaceid_e, type_e, campaign_e, region_e, opt_e, type_c] in join_dp
            if campaign_e == campaign
        ]
        df_filtered = pl.LazyFrame(filtered, orient="row")

        # Build context
        context = dp.Context.compositor(
            data=df_filtered,
            privacy_unit=dp.unit_of(contributions=5),
            privacy_loss=dp.loss_of(epsilon=epsilon),
            split_evenly_over=split_evenly_over,
        )

        # Perform DP query
        count_conversions = context.query().select(dp.len())
        dp_count = count_conversions.release().collect()['len'][0]

        comparison.append({
            'campaign': campaign,
            'non_dp_count': len(filtered),
            'dp_count': dp_count
        })

    return comparison


def homomorphic_encryption_workflow(events, conversions):
    """
    Apply homomorphic encryption to conversion data and compare with reference workflow.

    Args:
        events: List of engagement events
        conversions: List of conversion events

    Returns:
        dict with decrypted results, comparison dataframe, and execution times
    """
    campaigns = ['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Purple']

    # --------------------------
    # 1. Reference (non-HE) workflow
    # --------------------------
    start_time_ref = time.perf_counter()

    join_he_ref = [
        [spaceid_e, type_e, campaign_e, type_c]
        for (spaceid_e, key_e, type_e, campaign_e, region_e, opt_e) in events
        for (spaceid_c, key_c, type_c) in conversions
        if key_e == key_c
    ]

    aggregate_he_ref = [
        [
            campaign,
            sum([
                1
                for (_, _, campaign_, event_type) in join_he_ref
                if campaign == campaign_ and event_type == 'Purchase'
            ])
        ]
        for campaign in campaigns
    ]

    end_time_ref = time.perf_counter()
    ref_exec_time = end_time_ref - start_time_ref

    print(f"Execution time in seconds of reference workflow: {ref_exec_time:.6f}")

    # --------------------------
    # 2. Homomorphic Encryption (HE) workflow
    # --------------------------
    secret_key = pailliers.secret(256)
    public_key = pailliers.public(secret_key)

    start_time_he = time.perf_counter()

    conversions_enc = [
        [
            spaceid_c,
            key_c,
            pailliers.encrypt(public_key, 1 if event_type == 'Purchase' else 0),
            pailliers.encrypt(public_key, 1 if event_type == 'Subscription' else 0)
        ]
        for (spaceid_c, key_c, event_type) in tqdm(conversions, desc="Encrypting conversions")
    ]

    join_he = [
        [spaceid_e, type_e, campaign_e, count_p, count_s]
        for (spaceid_e, key_e, type_e, campaign_e, region_e, age_e) in events
        for (spaceid_c, key_c, count_p, count_s) in conversions_enc
        if key_e == key_c
    ]

    aggregate_he_enc = [
        [
            campaign,
            sum([
                count_p
                for (_, _, campaign_, count_p, _) in join_he
                if campaign == campaign_
            ], start=pailliers.encrypt(public_key, 0))  # Start with encrypted 0
        ]
        for campaign in campaigns
    ]

    aggregate_he_dec = [
        {
            'campaign': campaign,
            'purchase_count': pailliers.decrypt(secret_key, count)
        }
        for (campaign, count) in aggregate_he_enc
    ]

    end_time_he = time.perf_counter()
    he_exec_time = end_time_he - start_time_he

    print(f"Execution time in seconds of encrypted workflow: {he_exec_time:.6f}")

    # --------------------------
    # 3. Comparison table (non-HE vs HE)
    # --------------------------
    df_comparison_he = pd.DataFrame([
        (campaign, total_ref, total_dec['purchase_count'])
        for ((campaign, total_ref), total_dec) in zip(aggregate_he_ref, aggregate_he_dec)
    ], columns=["event_properties.promotion_name", "non-HE", "HE"])

    # --------------------------
    # 4. Plot comparison
    # --------------------------
    def plot_comparison_he(df):
        x = np.arange(len(campaigns))
        fig, ax = plt.subplots()
        bar_width = 0.35
        rects1 = ax.bar(x - bar_width/2, df['non-HE'], bar_width, label='non-HE')
        rects2 = ax.bar(x + bar_width/2, df['HE'], bar_width, label='HE')
        ax.set_ylabel('Conversion count')
        ax.set_title('Conversion count for each campaign')
        ax.set_xticks(x)
        ax.set_xticklabels(campaigns)
        ax.legend()
        fig.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return img_base64

    plot_comparison_he(df_comparison_he)

    # --------------------------
    # 5. Return everything
    # --------------------------
    img_b64 = plot_comparison_he(df_comparison_he)

    return {
        "results_decrypted": aggregate_he_dec,
        "comparison_table": df_comparison_he.to_dict(orient="records"),
        "execution_time": {
            "reference": ref_exec_time,
            "encrypted": he_exec_time
        },
        "chart_base64": img_b64
    }