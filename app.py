import streamlit as st
import pandas as pd

# ---------------- CONFIGURATION DATA ----------------
headon_dict = {
    "headlessYield": 0.675, "headWasteYield": 0.315, "skin&boneYield": 0.23, "proteinRecoveryYield": 0.22, 
    "surimiYield": 0.435, "fishMealYield": 0.26, "fishOilYield": 0.0019915, "headWasteTransferPrice": 26, 
    "skin&boneTransferPrice": 24, "proteinRecoveryTransferPrice": 14, "surimiAdditives&PM": 16.2105, 
    "fishMealAdditives&PM": 0.8488, "fishOilAdditives&PM": 5, "rawToHeadlessOH": 4.5, "surimiOH": 45, 
    "fmOH": 24, "foOH": 0, "surimiSelling": 380, "fmSelling": 135, "foSelling": 250
}

headless_dict = {
    "headlessYield": 0.93, "headWasteYield": 0, "skin&boneYield": 0.22515894, "proteinRecoveryYield": 0.12617924, 
    "surimiYield": 0.5320549630844955, "fishMealYield": 0.26, "fishOilYield": 0.0019915, "headWasteTransferPrice": 26, 
    "skin&boneTransferPrice": 23, "proteinRecoveryTransferPrice": 14, "surimiAdditives&PM": 16.2105, 
    "fishMealAdditives&PM": 0.8488, "fishOilAdditives&PM": 5, "rawToHeadlessOH": 4.5, "surimiOH": 24, 
    "fmOH": 22, "foOH": 0, "surimiSelling": 233.875, "fmSelling": 135, "foSelling": 250
}

def chooseSettings(fishType):
    return headon_dict if fishType == "headon" else headless_dict

# ---------------- CORE CALCULATIONS ----------------
def calculateQuantity(raw_qty, setting):
    final_qty = {}
    final_qty["headlessQty"] = raw_qty * setting["headlessYield"]
    final_qty["headwasteQty"] = raw_qty * setting["headWasteYield"]
    final_qty["unallocatedQty"] = raw_qty - final_qty["headlessQty"] - final_qty["headwasteQty"]
    final_qty["skin&boneQty"] = final_qty["headlessQty"] * setting["skin&boneYield"]
    final_qty["proteinRecoveryQty"] = final_qty["headlessQty"] * setting["proteinRecoveryYield"]
    final_qty["surimiQty"] = final_qty["headlessQty"] * setting["surimiYield"]
    final_qty["washingLossQty"] = final_qty["headlessQty"] - (final_qty["skin&boneQty"] + final_qty["proteinRecoveryQty"] + final_qty["surimiQty"])
    final_qty["fmInput"] = final_qty["headwasteQty"] + final_qty["skin&boneQty"] + final_qty["proteinRecoveryQty"]
    final_qty["fmQty"] = final_qty["fmInput"] * setting["fishMealYield"]
    final_qty["foQty"] = final_qty["fmInput"] * setting["fishOilYield"]
    return final_qty

def costCalculation(raw_qty, raw_rate, setting, quantity):
    cost = {}
    cost["raw_fish_cost"] = raw_qty * raw_rate
    cost["transfer_value"] = (quantity["headwasteQty"] * setting["headWasteTransferPrice"]) + (quantity["skin&boneQty"] * setting["skin&boneTransferPrice"]) + (quantity["proteinRecoveryQty"] * setting["proteinRecoveryTransferPrice"])
    cost["surimi_rmc"] = cost["raw_fish_cost"] + (quantity["surimiQty"] * setting["surimiAdditives&PM"]) - cost["transfer_value"]
    cost["fishmeal_rmc"] = cost["transfer_value"] + (quantity["fmQty"] * setting["fishMealAdditives&PM"])
    cost["fishoil_rmc"] = quantity["foQty"] * setting["fishOilAdditives&PM"]
    cost["surimi_overhead"] = (raw_qty * setting["rawToHeadlessOH"]) + (quantity["surimiQty"] * setting["surimiOH"])
    cost["fishmeal_overhead"] = quantity["fmQty"] * setting["fmOH"]
    cost["fishoil_overhead"] = quantity["foQty"] * setting["foOH"]
    return cost

def productResult(revenue, rmc, overhead):
    profit = revenue - rmc - overhead
    margin = (profit / revenue) * 100 if revenue > 0 else 0
    return {"revenue": revenue, "rmc": rmc, "overhead": overhead, "profit": profit, "margin": margin}

def calculateMargin(quantity, cost, setting):
    result = {}
    result["surimi"] = productResult(quantity["surimiQty"] * setting["surimiSelling"], cost["surimi_rmc"], cost["surimi_overhead"])
    result["fishmeal"] = productResult(quantity["fmQty"] * setting["fmSelling"], cost["fishmeal_rmc"], cost["fishmeal_overhead"])
    result["fishoil"] = productResult(quantity["foQty"] * setting["foSelling"], cost["fishoil_rmc"], cost["fishoil_overhead"])
    
    products = [result["surimi"], result["fishmeal"], result["fishoil"]]
    result["total"] = productResult(
        sum(p["revenue"] for p in products),
        sum(p["rmc"] for p in products),
        sum(p["overhead"] for p in products),
    )
    return result

# ---------------- STREAMLIT WEB UI ----------------
st.set_page_config(page_title="Fish Processing Margin Calculator", layout="centered")
st.title("🐟 Fish Processing Margin Calculator")
st.caption("Enter your raw production metrics below to evaluate margins.")

# Sidebar / Input panel
st.sidebar.header("🔧 Input Configurations")
fishType = st.sidebar.selectbox("Fish Type", options=["headon", "headless"])
raw_qty = st.sidebar.number_input("Raw Fish Quantity (kg)", min_value=0.1, value=1000.0, step=50.0)
raw_rate = st.sidebar.number_input("Raw Fish Rate (Rs/kg)", min_value=0.1, value=120.0, step=5.0)

if st.sidebar.button("Calculate Margins", type="primary"):
    setting = chooseSettings(fishType)
    quantity = calculateQuantity(raw_qty, setting)
    cost = costCalculation(raw_qty, raw_rate, setting, quantity)
    margin = calculateMargin(quantity, cost, setting)
    
    # Process data into a clean structure for web table display
    products_display = [
        ("Surimi", "surimi"),
        ("Fish meal", "fishmeal"),
        ("Fish oil", "fishoil"),
        ("TOTAL", "total")
    ]
    
    table_data = []
    for label, key in products_display:
        r = margin[key]
        table_data.append({
            "Product": label,
            "Revenue (Rs)": round(r['revenue'], 2),
            "RMC (Rs)": round(r['rmc'], 2),
            "Overhead (Rs)": round(r['overhead'], 2),
            "Profit (Rs)": round(r['profit'], 2),
            "Margin (%)": f"{round(r['margin'], 2)}%"
        })
    
    df = pd.DataFrame(table_data)
    
    st.subheader("📊 Product Margins Report")
    st.dataframe(df, hide_index=True, use_container_width=True)
