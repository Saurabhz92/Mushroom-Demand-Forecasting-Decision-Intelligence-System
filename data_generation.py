import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

# Configuration
NUM_DAYS = 360  # 1 year approx
START_DATE = datetime.today() - timedelta(days=NUM_DAYS)
REGIONS = ['Pune', 'Nashik', 'Mumbai', 'Nagpur', 'Aurangabad', 'Kolhapur', 'Solapur', 'Amravati', 'Nanded', 'Jalgaon']
MANDIS = {r: f"MANDI_{r.upper()}" for r in REGIONS}
SKUS = ['MUSH-200g', 'MUSH-250g', 'MUSH-500g', 'MUSH-1kg', 'MUSH-5kg']
PACKAGING_MAP = {
    'MUSH-200g': 0.2, 'MUSH-250g': 0.25, 'MUSH-500g': 0.5, 
    'MUSH-1kg': 1.0, 'MUSH-5kg': 5.0
}
CHANNELS = ['B2B', 'B2C']
STORES_PER_REGION = 5  # Simplified for PoC

# Seasonality & Event Config
SEASONALITY_MONTHS = {11: 1.2, 12: 1.3, 1: 1.1} # Nov-Jan wedding season
WEEKDAY_FACTORS = {
    'B2B': [1.1, 1.1, 1.1, 1.2, 1.3, 0.8, 0.7], # Mon-Sun, peak Thu-Fri for weekend events
    'B2C': [0.8, 0.8, 0.8, 0.9, 1.1, 1.3, 1.2]  # Peak Sat-Sun
}

def generate_historical_sales():
    print("Generating historical_sales.csv...")
    data = []
    
    for day_offset in range(NUM_DAYS):
        curr_date = START_DATE + timedelta(days=day_offset)
        date_str = curr_date.strftime('%Y-%m-%d')
        weekday = curr_date.weekday() # 0=Mon, 6=Sun
        month = curr_date.month
        
        # Global Daily Features
        panchang_fasting = 1 if random.random() < 0.15 else 0 # ~15% days are fasting
        wedding_density = random.uniform(0.0, 0.3)
        if month in SEASONALITY_MONTHS:
            wedding_density += random.uniform(0.3, 0.6)
        
        festival_flag = 1 if random.random() < 0.05 else 0
        logistics_disruption = 1 if random.random() < 0.02 else 0 # Rare
        
        # Weather (Base)
        base_temp = 25 + 10 * np.sin(2 * np.pi * day_offset / 365) # Seasonal temp
        
        for region in REGIONS:
            mandi_id = MANDIS[region]
            
            # Region-specific weather noise
            temp_max = base_temp + random.uniform(-3, 5)
            temp_min = temp_max - random.uniform(8, 15)
            humidity = random.uniform(30, 90)
            rainfall = 0.0
            if humidity > 70 and random.random() < 0.3:
                rainfall = random.uniform(5, 100)
            
            # Mandi Price
            mandi_price_base = 120 # Base price per kg
            mandi_volatility = random.uniform(0.9, 1.1)
            if festival_flag: mandi_volatility += 0.1
            mandi_price = mandi_price_base * mandi_volatility
            mandi_change = random.uniform(-10, 10)
            
            for sku in SKUS:
                pkg_size = PACKAGING_MAP[sku]
                
                for channel in CHANNELS:
                    # Generate multiple stores per region/channel if needed, 
                    # but prompt asks for row-level daily sales per region-sku-channel-store_id
                    # We will simulate 1 aggregate row per channel per region to keep file size manageable for PoC 
                    # OR a few stores. Let's do 2 stores per channel per region.
                    
                    for store_idx in range(2):
                        store_id = f"{region}_{channel}_{store_idx}"
                        
                        # Demand Generation Logic
                        base_demand = 50 if channel == 'B2C' else 200 # Units
                        
                        # Seasonality
                        season_factor = SEASONALITY_MONTHS.get(month, 1.0)
                        weekday_factor = WEEKDAY_FACTORS[channel][weekday]
                        
                        # Events
                        fasting_impact = 0.7 if (panchang_fasting and channel == 'B2C') else 1.0
                        wedding_impact = (1.0 + wedding_density) if channel == 'B2B' else 1.0
                        
                        # Price Elasticity
                        optimal_price = mandi_price * (1.2 if channel == 'B2B' else 1.5) + (pkg_size * 10) # Simple markup
                        price_offered = optimal_price * random.uniform(0.95, 1.05)
                        elasticity = -1.5 if channel == 'B2C' else -0.8
                        price_factor = (price_offered / optimal_price) ** elasticity
                        
                        # Final Demand
                        noise = random.uniform(0.8, 1.2)
                        demand_units = int(base_demand * season_factor * weekday_factor * fasting_impact * wedding_impact * price_factor * noise)
                        
                        # Logistics Disruption
                        if logistics_disruption:
                            inventory_received = demand_units * pkg_size * random.uniform(0.5, 0.8) # Shortage
                        else:
                            inventory_received = demand_units * pkg_size * random.uniform(1.0, 1.2) # Overstock slightly
                        
                        sales_units = min(demand_units, int(inventory_received / pkg_size))
                        sales_kg = sales_units * pkg_size
                        
                        # Wastage
                        unsold_kg = max(0, inventory_received - sales_kg)
                        decay_rate = 0.1 + (0.05 if temp_max > 30 else 0) + (0.05 if humidity > 80 else 0)
                        wastage_kg = unsold_kg * decay_rate
                        
                        row = {
                            'date': date_str,
                            'region_id': region,
                            'mandi_id': mandi_id,
                            'store_id': store_id,
                            'sku_id': sku,
                            'channel': channel,
                            'packaging': f"{int(pkg_size*1000) if pkg_size < 1 else int(pkg_size)}g" if pkg_size < 1 else f"{int(pkg_size)}kg",
                            'sales_units': sales_units,
                            'sales_kg': round(sales_kg, 2),
                            'inventory_received_kg': round(inventory_received, 2),
                            'wastage_kg': round(wastage_kg, 2),
                            'price_offered_per_kg': round(price_offered, 2),
                            'optimal_price_per_kg': round(optimal_price, 2),
                            'b2b_b2c_ratio': 0.8 if channel == 'B2B' else 0.2, # Simplified
                            'mandi_price_per_kg': round(mandi_price, 2),
                            'mandi_price_change_1d': round(mandi_change, 2),
                            'panchang_fasting_flag': panchang_fasting,
                            'wedding_density_30d': round(wedding_density, 2),
                            'festival_flag': festival_flag,
                            'temp_max_c': round(temp_max, 1),
                            'temp_min_c': round(temp_min, 1),
                            'humidity_avg': round(humidity, 1),
                            'rainfall_mm': round(rainfall, 1),
                            'logistics_disruption_flag': logistics_disruption,
                            'volatility_score_14d': round(random.uniform(0, 1), 2),
                            'packaging_pref_score': round(random.uniform(0.3, 0.9), 2),
                            'lag_1_sales': int(sales_units * random.uniform(0.9, 1.1)), # Mock lag
                            'lag_7_sales_mean': round(sales_units * random.uniform(0.8, 1.2), 2), # Mock lag
                            'label_daily_demand': demand_units
                        }
                        data.append(row)
                        
    df = pd.DataFrame(data)
    df.to_csv('historical_sales.csv', index=False)
    print(f"Saved historical_sales.csv with {len(df)} rows.")

def generate_intraday_telemetry():
    print("Generating intraday_telemetry.csv...")
    data = []
    
    # Generate for the last 7 days only for high frequency
    start_dt = datetime.now() - timedelta(days=7)
    
    for hour_offset in range(7 * 24):
        curr_dt = start_dt + timedelta(hours=hour_offset)
        dt_str = curr_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Base conditions
        is_daytime = 8 <= curr_dt.hour <= 20
        
        for region in REGIONS:
            # Intraday variations
            mandi_price = 120 + random.uniform(-5, 5)
            
            # Weather updates
            temp = 25 + (5 if is_daytime else -5) + random.uniform(-2, 2)
            humidity = 60 + random.uniform(-10, 10)
            
            # Events
            event = 'none'
            if random.random() < 0.01: event = 'heavy_rain'
            if random.random() < 0.005: event = 'strike'
            
            # POS Transactions (proxy for demand velocity)
            pos_tx = int(random.normalvariate(50, 15)) if is_daytime else int(random.normalvariate(5, 2))
            if event == 'heavy_rain': pos_tx = int(pos_tx * 0.5)
            
            # Logistics
            delay = 0
            if event == 'strike': delay = random.randint(60, 300)
            if random.random() < 0.05: delay = random.randint(10, 45)
            
            # Baseline Pred vs Actual
            baseline = 1000 # Aggregate daily prediction for region
            # Hourly fraction of daily sales (simple curve)
            hourly_profile = [0.01]*8 + [0.05, 0.08, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.08, 0.05, 0.02, 0.01] + [0.0]*4
            expected_fraction = hourly_profile[curr_dt.hour] if curr_dt.hour < 24 else 0
            
            baseline_hourly = baseline * expected_fraction
            actual_sales = int(baseline_hourly * random.uniform(0.8, 1.2))
            
            row = {
                'datetime': dt_str,
                'region_id': region,
                'mandi_price_per_kg': round(mandi_price, 2),
                'pos_transactions_last_hour': pos_tx,
                'vehicle_delay_minutes': delay,
                'weather_now_temp': round(temp, 1),
                'weather_now_humidity': round(humidity, 1),
                'logistics_disruption_flag': 1 if delay > 60 else 0,
                'intraday_baseline_pred': round(baseline_hourly, 2),
                'intraday_actual_sales_partial': actual_sales, # This would be cumulative in real life, but simplified here
                'intraday_event': event
            }
            data.append(row)
            
    df = pd.DataFrame(data)
    df.to_csv('intraday_telemetry.csv', index=False)
    print(f"Saved intraday_telemetry.csv with {len(df)} rows.")

if __name__ == "__main__":
    generate_historical_sales()
    generate_intraday_telemetry()
