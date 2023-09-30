import json
import login


def get_plans(plan_data):

    accounts =plan_data['accounts']
    account = accounts[0]
    plans = account['account']['plans']
    return plans


def get_plan_detail(plans):

    for plan in plans:
        plan_detail = plan['plan_detail']
    return plan_detail


def get_e_contract(plan_detail):

    e_contract = plan_detail['electricity_contract']
    return e_contract


def get_tariff_period(e_contract):

    tariff_period = e_contract['tariff_period']

    # Rate (include Daily supply charge & time of use)
    rates = []
    for tariff in tariff_period:

        # Daily supply charge
        if 'daily_supply_charges' in tariff:
            daily_supply_charge = tariff['daily_supply_charges']
            rates.append({'daily_supply_charge': daily_supply_charge})

        # Time of use rate:
        rate_block_u_type = tariff['rate_block_u_type']

            # Single_rate
        if rate_block_u_type == 'singleRate':
            for price in tariff['single_rate']['rates']:
                unit_price = price['unit_price']
                # block_period = tariff['period']
                # block_volume = tariff['rated']['volume']
                rates.append({'type': 'Peak', 'unit_price': unit_price})

            # Time of use
        elif rate_block_u_type == 'timeOfUseRates':
            for tou in tariff['time_of_use_rates']:
                tou_type = tou['type']
                rate = tou['rates']['unit_price']
                rates.append({'type': tou_type, 'unit_price': rate})

            # Demand charge
        if 'demand_charges' in tariff:
            for demand in tariff['demand_charges']:
                demand_display_name = demand['display_name']
                demand_amount = demand['amount']
                demand_start_time = demand['start_time']
                demand_end_time = demand['end_time']
                rates.append({'demand_charge': demand_display_name,
                              'amount': demand_amount,
                              'start_time': demand_start_time,
                              'end_time': demand_end_time})
    return rates


def get_controlled_load(e_contract):

    controlled_load = []
    if "controlled_load" in e_contract:
        for control_load in e_contract['controlled_load']:

            # Time of use rate:
            rate_block_u_type = control_load['rate_block_u_type']

                # Single_rate
            if rate_block_u_type == 'singleRate':
                daily_supply_charge = control_load['single_rate']['daily_supply_charge']
                controlled_load.append({'daily_supply_charge': daily_supply_charge})
                for price in control_load['single_rate']['rates']:
                    unit_price = price['unit_price']
                    controlled_load.append({'type': 'Peak', 'unit_price': unit_price})

                # Time of use
            elif rate_block_u_type == 'timeOfUseRates':
                daily_supply_charge = control_load['time_of_use']['daily_supply_charge']
                controlled_load.append({'daily_supply_charge': daily_supply_charge})
                for tou in control_load['time_of_use_rates']:
                    tou_type = tou['type']
                    rate = tou['rates']['unit_price']
                    controlled_load.append({'type': tou_type, 'unit_price': rate})
    return controlled_load

def parse_discount(plan_detail: json):

    if 'discounts' in plan_detail:
        discount = plan_detail['discounts'][0]
        discount_description = discount['description']
        discount_amount = discount['fixed_amount']['amount']
        discounts = ({'discount': discount_description, 'amount': discount_amount})
    else:
        discounts = []
    return discounts


def parse_solar(feeds):

    solar = []
    feeds = e_contract['solar_feed_in_tariff']
    for feed in feeds:
        parsed_feed = {}
        if 'display_name' in feed:
            parsed_feed['name'] = feed['display_name']
        if 'amount' in feed['single_tariff']:
            parsed_feed['amount'] = feed['single_tariff']['amount']
        solar.append(parsed_feed)
    return solar


def get_pricing(rates, controlled_load, solar):

    pricing = {'tariff': rates,
               'controlled_load': controlled_load,
               'solar_feed_in': solar}
    return pricing


def get_customer_type(service_point_list):

    service_points = service_point_list['service_points']
    for service_point in service_points:
        customer_type = service_point['service_point']['consumer_profile']['classification']
    return customer_type


def get_overview(customer_type, plans, plan_detail):

    overview_display= []
    customer_type = customer_type
    fuel_type = plan_detail['fuel_type']
    # for overview in plans:
    display_name = plans[0]['plan_overview']['display_name']
    plan_start_date = plans[0]['plan_overview']['start_date']
    plan_end_date = plans[0]['plan_overview']['end_date']

    overview_display.append({'tariff': display_name,
                             'fuel': fuel_type, 'customer_type': customer_type,
                             'plan_start_day': plan_start_date,
                             'plan_end_date': plan_end_date})
    return overview_display


def get_payment(e_contract):

    payment_opt = e_contract['payment_option']
    return payment_opt


access_token = login.get_access_token()
plans_data = login.fetch_and_save_plan_info(access_token)
plans = get_plans(plans_data)
plan_detail = get_plan_detail(plans)
e_contract = get_e_contract(plan_detail)

solar = parse_solar(e_contract)
discount = parse_discount(plan_detail)
rates = get_tariff_period(e_contract)
controledload = get_controlled_load(e_contract)
pricing = get_pricing(rates, controledload, solar)

service_point_list = login.fetch_service_point(access_token)
customer_type = get_customer_type(service_point_list)
overview = get_overview(customer_type=customer_type, plans=plans, plan_detail=plan_detail)

payment_option = get_payment(e_contract=e_contract)


print(overview)
# print(discount)
# print(pricing)
# print(payment_option)