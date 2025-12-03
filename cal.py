from flask import Flask, render_template, request, jsonify
import math
import requests

app = Flask(__name__)

# ---------------- SAFE MATH FUNCTIONS ----------------
SAFE_NAMES = {
    k: getattr(math, k) for k in [
        "sin","cos","tan","asin","acos","atan","sinh","cosh","tanh",
        "log","log10","sqrt","factorial","degrees","radians","fabs","floor","ceil"
    ] if hasattr(math, k)
}
SAFE_NAMES.update({
    "ln": math.log,
    "log2": getattr(math, "log2", lambda x: math.log(x, 2)),
    "pi": math.pi,
    "e": math.e,
    "pow": pow,
    "abs": abs
})

def safe_eval(expr):
    """Evaluate math expressions using a restricted name space."""
    expr = expr.replace("×", "*").replace("÷", "/").replace("−", "-")
    try:
        return eval(expr, {"__builtins__": {}}, SAFE_NAMES)
    except Exception:
        return "Error"

# ---------------- UNIT CONVERTER ----------------
def convert_unit(value, category, frm, to):
    try:
        if category == "length":
            table = {
                "m":1,"cm":0.01,"mm":0.001,"km":1000,
                "in":0.0254,"ft":0.3048,"yd":0.9144,"mi":1609.344
            }
        elif category == "weight":
            table = {
                "kg":1,"g":0.001,"mg":1e-6,
                "lb":0.453592,"oz":0.0283495
            }
        elif category == "volume":
            table = {"l":1,"ml":0.001,"m3":1000,"cup":0.24,"pt":0.473176,"gal":3.78541}
        elif category == "temperature":
            if frm == to:
                return value
            if frm == "C": c = value
            elif frm == "F": c = (value - 32) * 5/9
            elif frm == "K": c = value - 273.15
            if to == "C": return round(c,6)
            if to == "F": return round(c * 9/5 + 32,6)
            if to == "K": return round(c + 273.15,6)
        else:
            return "Error"
        return round(value * table[frm] / table[to], 6)
    except Exception:
        return "Error"
00
# ------------------- LIVE CURRENCY FETCH -------------------0
# Using Frankfurter (stable free API)
EXCHANGE_API = "https://api.frankfurter.dev/latest"

# Realistic extended fallback rates (rates relative to EUR)
# These are approximate market-like numbers used only as a fallback.
FALLBACK_RATES = {
    "EUR": 1.0,
    "USD": 1.07,
    "INR": 89.0,
    "GBP": 0.86,
    "JPY": 157.0,
    "AUD": 1.62,
    "CAD": 1.36,
    "CHF": 0.95,
    "CNY": 7.63,
    "HKD": 8.36,
    "SGD": 1.45,
    "NZD": 1.75,
    "KRW": 1420.0,
    "BRL": 5.32,
    "ZAR": 19.0,
    "RUB": 95.0,
    "SEK": 11.0,
    "NOK": 11.5,
    "DKK": 7.45,
    "MXN": 18.5,
    "TRY": 36.0,
    "IDR": 18000.0,
    "MYR": 4.80,
    "THB": 38.0,
    "PHP": 58.0,
    "AED": 3.94,
    "SAR": 4.01,
    "ILS": 3.90,
    "PLN": 4.30,
    "CZK": 24.5,
    "HUF": 420.0,
    "CLP": 980.0,
    "COP": 4200.0,
    "VND": 27000.0,
    "PEN": 3.80,
    "ARS": 110.0,
    "EGP": 48.0,
    "NGN": 900.0,
    "KWD": 0.33,
    "BHD": 0.40,
    "OMR": 0.42,
    "BDT": 119.0
}

def fetch_all_currencies():
    """
    Fetch rates from Frankfurter. Frankfurter returns JSON with 'rates' and 'base'.
    We'll return a dict mapping currency code -> rate relative to base (EUR).
    If the API fails or returns empty, return FALLBACK_RATES.
    """
    try:
        res = requests.get(EXCHANGE_API, timeout=8)
        data = res.json()
        if data and "rates" in data:
            rates = dict(data["rates"])
            base = data.get("base", "EUR")
            # frankfurter does not include base in rates, ensure base is present with value 1.0
            rates[base] = 1.0
            return rates
    except Exception:
        pass
    # fallback
    return dict(FALLBACK_RATES)

# ---------------- CURRENCY CONVERSION ----------------
def convert_currency(amount, frm, to, rates):
    """
    Convert using rates relative to the same base (EUR).
    Algorithm: convert amount from 'frm' to base (EUR) then to 'to':
      amount_in_base = amount / rates[frm]
      result = amount_in_base * rates[to]
    """
    try:
        if frm == to:
            return round(amount, 6)
        if frm not in rates or to not in rates:
            return "RateMissing"
        frm_rate = rates[frm]
        to_rate = rates[to]
        base_val = amount / frm_rate
        return round(base_val * to_rate, 6)
    except Exception:
        return "Error"

# ---------------- MAIN ROUTE ----------------
@app.route("/", methods=["GET","POST"])
def index():
    tab = request.form.get("tab", "calc")   # calc, unit, currency

    # Provide defaults and current data needed by template
    rates = fetch_all_currencies() or FALLBACK_RATES
    currency_list = sorted(rates.keys())

    # Calculator tab (server-side fallback if form posts)
    if tab == "calc":
        current = request.form.get("display", "0")
        btn = request.form.get("btn")
        kb = request.form.get("keyboard_input", "")
        display = current

        # Keyboard input
        if kb != "":
            if kb in ["⌫", "BACKSPACE", "\b"]:
                display = current[:-1] if len(current) > 1 else "0"
            elif kb in ["ENTER", "="]:
                display = str(safe_eval(current))
            else:
                display = kb if current == "0" else current + kb
            return render_template("format.html", tab="calc", display=display,
                                   currency_list=currency_list)

        # Button input
        if btn in ["C", "CE"]:
            display = "0"
        elif btn == "⌫":
            display = current[:-1] if len(current) > 1 else "0"
        elif btn == "=":
            display = str(safe_eval(current))
        elif btn == "x²":
            try:
                display = str(float(current)**2)
            except:
                display = "Error"
        elif btn == "√":
            try:
                display = str(math.sqrt(float(current)))
            except:
                display = "Error"
        elif btn == "1/x":
            try:
                display = str(1 / float(current))
            except:
                display = "Error"
        elif btn == "+/-":
            display = current[1:] if current.startswith("-") else "-" + current
        elif btn:
            display = btn if current == "0" else current + btn

        return render_template("format.html", tab="calc", display=display,
                               currency_list=currency_list)

    # Unit converter tab
    if tab == "unit":
        cat = request.form.get("unit_category", "length")
        frm = request.form.get("unit_from", "")
        to = request.form.get("unit_to", "")
        val = request.form.get("unit_value", "")
        result = ""
        if request.form.get("convert_unit_btn"):
            try:
                result = convert_unit(float(val), cat, frm, to)
            except:
                result = "Error"
        return render_template("format.html", tab="unit",
                               unit_category=cat, unit_from=frm,
                               unit_to=to, unit_value=val, unit_result=result,
                               currency_list=currency_list)

    # Currency converter tab
    if tab == "currency":
        amount = request.form.get("amount", "")
        frm = request.form.get("from_currency", "USD")
        to = request.form.get("to_currency", "EUR")
        result = ""
        live_rates = None

        # fetch on demand (button)
        if request.form.get("fetch_rates_btn"):
            live_rates = fetch_all_currencies()

        if request.form.get("convert_currency_btn"):
            try:
                live_rates = fetch_all_currencies()
                if live_rates is None or len(live_rates) == 0:
                    result = "API Error (Try Again)"
                else:
                    conv = convert_currency(float(amount), frm, to, live_rates)
                    result = conv
            except:
                result = "Error"

        if live_rates is None:
            live_rates = fetch_all_currencies()

        currency_list = sorted(live_rates.keys()) if live_rates else currency_list
        return render_template("format.html", tab="currency",
                               amount=amount, from_currency=frm, to_currency=to,
                               currency_list=currency_list, currency_result=result)

    return "Invalid Tab", 400

# Endpoint for frontend to fetch live rates in JSON
@app.route("/rates")
def rates_api():
    r = fetch_all_currencies()
    if r:
        # Always return success True with rates (either live or fallback) so frontend can proceed
        return jsonify({'success': True, 'rates': r})
    return jsonify({'success': False, 'rates': {}})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
