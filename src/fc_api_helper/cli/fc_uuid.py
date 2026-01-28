"""fc-uuid CLI tool for selecting database table UUIDs interactively."""

import subprocess
import sys

# Configuration
DB_URL = "postgresql://fundcraft_admin:fundcraft_admin@localhost:5432/fundcraft"

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
# Unified mapping of table names to their metadata:
#   - "identifier": the most readable column to display (for fzf selection)
#   - "joins": SQL JOIN clause(s) to reach fundcraft_client (empty string if direct/none)
#   - "client_filter": column expression that equals fundcraft_client.uuid (empty string if no path)
#
# Usage:
#   config = TABLE_CONFIG["fundcraft_capitalcall"]
#   identifier = config["identifier"]  # "capital_call_code"
#   if config["client_filter"]:  # has client join path
#       query = f"SELECT t.* FROM django.{table} t {config['joins']} WHERE {config['client_filter']} = '{client_uuid}'"
# =============================================================================

TABLE_CONFIG = {
    # DIRECT TO CLIENT (via uuid/client_id column)
    "fundcraft_client": {"identifier": "slug", "joins": "", "client_filter": "t.uuid"},
    "fundcraft_admin_report": {"identifier": "id", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_annualaccountsprocess": {"identifier": "id", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_apiclientintegration": {"identifier": "service_name", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_billableevent": {"identifier": "currency_code", "joins": "", "client_filter": "t.client_uuid"},
    "fundcraft_client_employees": {"identifier": "id", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_dataroom": {"identifier": "name", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_eventactionlog": {"identifier": "id", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_fcprocessexecution": {"identifier": "codename", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_freescoutmailbox": {"identifier": "name", "joins": "", "client_filter": "t.owner_client_id"},
    "fundcraft_investortype": {"identifier": "name", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_kpi_report": {"identifier": "id", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_kyc_document_type_master": {"identifier": "status", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_kyccorporateprocess": {"identifier": "id", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_kycindividualprocess": {"identifier": "id", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_lpportaltask": {"identifier": "status", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_nomineebeneficiary": {"identifier": "identifier", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_redemptionprocess": {"identifier": "redemption_code", "joins": "", "client_filter": "t.client_id"},
    "fundcraft_reportingtype_clients": {"identifier": "id", "joins": "", "client_filter": "t.client_id"},

    # DIRECT TO CLIENT (via id - needs join to get uuid)
    "fundcraft_classofshares": {"identifier": "share_name", "joins": "JOIN django.fundcraft_client cl ON cl.id = t.client_id", "client_filter": "cl.uuid"},
    "fundcraft_companyexternalinfo": {"identifier": "id", "joins": "JOIN django.fundcraft_client cl ON cl.id = t.client_id", "client_filter": "cl.uuid"},
    "fundcraft_emailinbox": {"identifier": "email", "joins": "JOIN django.fundcraft_client cl ON cl.id = t.client_id", "client_filter": "cl.uuid"},
    "fundcraft_fundclassofshares": {"identifier": "share_name", "joins": "JOIN django.fundcraft_client cl ON cl.id = t.client_id", "client_filter": "cl.uuid"},
    "fundcraft_fundexternalinfo": {"identifier": "id", "joins": "JOIN django.fundcraft_client cl ON cl.id = t.client_id", "client_filter": "cl.uuid"},
    "fundcraft_integrations_vestlane_credentials": {"identifier": "id", "joins": "JOIN django.fundcraft_client cl ON cl.id = t.client_id", "client_filter": "cl.uuid"},
    "fundcraft_personexternalinfo": {"identifier": "id", "joins": "JOIN django.fundcraft_client cl ON cl.id = t.client_id", "client_filter": "cl.uuid"},

    # VIA owner_client_id
    "fundcraft_company": {"identifier": "name", "joins": "", "client_filter": "t.owner_client_id"},
    "fundcraft_investment": {"identifier": "full_name", "joins": "", "client_filter": "t.owner_client_id"},
    "fundcraft_investor": {"identifier": "full_name", "joins": "", "client_filter": "t.owner_client_id"},
    "fundcraft_lp_portal_lp_account_structure": {"identifier": "name", "joins": "", "client_filter": "t.owner_client_id"},
    "fundcraft_person": {"identifier": "name", "joins": "", "client_filter": "t.owner_client_id"},

    # VIA company -> client
    "fundcraft_accountingtransactionsjournal": {"identifier": "reference", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_annualaccount": {"identifier": "id", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_bank": {"identifier": "bic_swift", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_companybankaccountinformation": {"identifier": "bank_name", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_companyblocked": {"identifier": "reason", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_companycontact": {"identifier": "full_name", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_companydocumentnotification": {"identifier": "id", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_companyexternaldocumenttargetssession": {"identifier": "status", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_companyimportlog": {"identifier": "id", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_companykycstatus": {"identifier": "id", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_companyscreeningongoingmonitoringrequestlog": {"identifier": "status", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_companystockexchangerelationship": {"identifier": "id", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_companysuspended": {"identifier": "reason", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_companyvaluation": {"identifier": "id", "joins": "JOIN django.fundcraft_company co ON co.id = t.target_company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_governingcompany": {"identifier": "id", "joins": "JOIN django.fundcraft_company co ON co.id = t.governed_company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_governingperson": {"identifier": "id", "joins": "JOIN django.fundcraft_company co ON co.id = t.governed_company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_legalcompanyresponsible": {"identifier": "classification", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_structure": {"identifier": "name", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},

    # VIA fund -> company -> client
    "fundcraft_fund": {"identifier": "aifm_code", "joins": "JOIN django.fundcraft_company co ON co.id = t.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_capitalcallshareholder": {"identifier": "payment_reference_code", "joins": "JOIN django.fundcraft_fund f ON f.id = t.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    # VIA structure_investment_vehicle -> structure -> company -> client
    "fundcraft_capitalcall": {"identifier": "capital_call_code", "joins": "JOIN django.fundcraft_structureinvestmentvehicle siv ON siv.id = t.structure_investment_vehicle_id JOIN django.fundcraft_structure s ON s.id = siv.structure_id JOIN django.fundcraft_company co ON co.id = s.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_distribution": {"identifier": "distribution_code", "joins": "JOIN django.fundcraft_structureinvestmentvehicle siv ON siv.id = t.structure_investment_vehicle_id JOIN django.fundcraft_structure s ON s.id = siv.structure_id JOIN django.fundcraft_company co ON co.id = s.company_id", "client_filter": "co.owner_client_id"},
    # VIA investor (investor_id INTEGER) -> client
    "fundcraft_distributionshareholder": {"identifier": "payment_reference_code", "joins": "JOIN django.fundcraft_investor inv ON inv.id = t.investor_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_fundclassofsharescategory": {"identifier": "category_name", "joins": "JOIN django.fundcraft_fund f ON f.id = t.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_fundclassofsharesgroup": {"identifier": "name", "joins": "JOIN django.fundcraft_fund f ON f.id = t.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_fundcommitmentfacility": {"identifier": "id", "joins": "JOIN django.fundcraft_fund f ON f.id = t.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_fundcustodian": {"identifier": "id", "joins": "JOIN django.fundcraft_fund f ON f.id = t.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_fundexcludablefromequalisation": {"identifier": "id", "joins": "JOIN django.fundcraft_fund f ON f.id = t.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_fundfcosrelationship": {"identifier": "id", "joins": "JOIN django.fundcraft_fund f ON f.id = t.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_investorfundbalance": {"identifier": "id", "joins": "JOIN django.fundcraft_fund f ON f.id = t.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_kpi_report_fund": {"identifier": "id", "joins": "JOIN django.fundcraft_fund f ON f.id = t.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_partneragreement": {"identifier": "id", "joins": "JOIN django.fundcraft_fund f ON f.id = t.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_paymentissuesresolutionprocess": {"identifier": "fc_template_code", "joins": "JOIN django.fundcraft_fund f ON f.id = t.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_compartmentrelationship": {"identifier": "id", "joins": "JOIN django.fundcraft_fund f ON f.id = t.umbrella_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_navchecklist": {"identifier": "is_discarded", "joins": "JOIN django.fundcraft_fund f ON f.id = t.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_navchecklistcheck": {"identifier": "title", "joins": "JOIN django.fundcraft_navchecklist nc ON nc.id = t.nav_checklist_id JOIN django.fundcraft_fund f ON f.id = nc.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_navchecklistcheckcomment": {"identifier": "id", "joins": "JOIN django.fundcraft_navchecklistcheck ncc ON ncc.id = t.check_id JOIN django.fundcraft_navchecklist nc ON nc.id = ncc.nav_checklist_id JOIN django.fundcraft_fund f ON f.id = nc.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_valuationprocess": {"identifier": "id", "joins": "JOIN django.fundcraft_fund f ON f.id = t.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_valuationstatement": {"identifier": "id", "joins": "JOIN django.fundcraft_valuationprocess vp ON vp.id = t.valuation_process_id JOIN django.fundcraft_fund f ON f.id = vp.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_valuationstatementline": {"identifier": "id", "joins": "JOIN django.fundcraft_valuationstatement vs ON vs.id = t.valuation_statement_id JOIN django.fundcraft_valuationprocess vp ON vp.id = vs.valuation_process_id JOIN django.fundcraft_fund f ON f.id = vp.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},

    # VIA investor -> client (investor_id as UUID/varchar)
    "fundcraft_directsubscription": {"identifier": "payment_reference_code", "joins": "JOIN django.fundcraft_investor inv ON inv.uuid = t.investor_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_investorfunddetail": {"identifier": "id", "joins": "JOIN django.fundcraft_investor inv ON inv.uuid = t.investor_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_navinvestor": {"identifier": "id", "joins": "JOIN django.fundcraft_investor inv ON inv.uuid = t.investor_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_navshareholder": {"identifier": "id", "joins": "JOIN django.fundcraft_investor inv ON inv.uuid = t.investor_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_reclassofshares": {"identifier": "id", "joins": "JOIN django.fundcraft_investor inv ON inv.uuid = t.investor_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_redemptioninvestor": {"identifier": "id", "joins": "JOIN django.fundcraft_investor inv ON inv.uuid = t.investor_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_transferofshareprocess": {"identifier": "transfer_of_shares_process_code", "joins": "JOIN django.fundcraft_investor inv ON inv.uuid = t.investor_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_valuationstatementshareholder": {"identifier": "id", "joins": "JOIN django.fundcraft_investor inv ON inv.uuid = t.investor_id", "client_filter": "inv.owner_client_id"},
    # VIA investor -> client (investor_id as INTEGER - join on inv.id)
    "fundcraft_investorbanckaccountinformation": {"identifier": "bank_name", "joins": "JOIN django.fundcraft_investor inv ON inv.id = t.investor_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_investorsubscription": {"identifier": "status", "joins": "JOIN django.fundcraft_investor inv ON inv.id = t.investor_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_transferofshare": {"identifier": "id", "joins": "JOIN django.fundcraft_investor inv ON inv.id = t.investor_seller_id", "client_filter": "inv.owner_client_id"},

    # VIA structure -> company -> client
    "fundcraft_conversionprocess": {"identifier": "id", "joins": "JOIN django.fundcraft_structure s ON s.id = t.structure_id JOIN django.fundcraft_company co ON co.id = s.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_employeestructurerelationship": {"identifier": "id", "joins": "JOIN django.fundcraft_structure s ON s.id = t.structure_id JOIN django.fundcraft_company co ON co.id = s.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_fcpermissionstructuregroupuser": {"identifier": "id", "joins": "JOIN django.fundcraft_structure s ON s.id = t.structure_id JOIN django.fundcraft_company co ON co.id = s.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_fcpermissionstructureuser": {"identifier": "id", "joins": "JOIN django.fundcraft_structure s ON s.id = t.structure_id JOIN django.fundcraft_company co ON co.id = s.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_investmentgroup": {"identifier": "name", "joins": "JOIN django.fundcraft_structure s ON s.id = t.structure_id JOIN django.fundcraft_company co ON co.id = s.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_kycprocess": {"identifier": "id", "joins": "JOIN django.fundcraft_structure s ON s.id = t.kyc_structure_id JOIN django.fundcraft_company co ON co.id = s.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_kyctargetstructure": {"identifier": "id", "joins": "JOIN django.fundcraft_structure s ON s.id = t.structure_id JOIN django.fundcraft_company co ON co.id = s.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_structurecontact": {"identifier": "full_name", "joins": "JOIN django.fundcraft_structure s ON s.id = t.structure_id JOIN django.fundcraft_company co ON co.id = s.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_structuredraft": {"identifier": "id", "joins": "JOIN django.fundcraft_structure s ON s.id = t.structure_id JOIN django.fundcraft_company co ON co.id = s.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_structureentity": {"identifier": "entity_type", "joins": "JOIN django.fundcraft_structure s ON s.id = t.structure_id JOIN django.fundcraft_company co ON co.id = s.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_structureinvestmentvehicle": {"identifier": "id", "joins": "JOIN django.fundcraft_structure s ON s.id = t.structure_id JOIN django.fundcraft_company co ON co.id = s.company_id", "client_filter": "co.owner_client_id"},

    # VIA person -> client
    "fundcraft_personbankaccountinformation": {"identifier": "bank_name", "joins": "JOIN django.fundcraft_person p ON p.id = t.person_id", "client_filter": "p.owner_client_id"},
    "fundcraft_personblocked": {"identifier": "reason", "joins": "JOIN django.fundcraft_person p ON p.id = t.person_id", "client_filter": "p.owner_client_id"},
    "fundcraft_personkycstatus": {"identifier": "id", "joins": "JOIN django.fundcraft_person p ON p.id = t.person_id", "client_filter": "p.owner_client_id"},
    "fundcraft_personscreeningongoingmonitoringrequestlog": {"identifier": "status", "joins": "JOIN django.fundcraft_person p ON p.id = t.person_id", "client_filter": "p.owner_client_id"},
    "fundcraft_personsuspended": {"identifier": "reason", "joins": "JOIN django.fundcraft_person p ON p.id = t.person_id", "client_filter": "p.owner_client_id"},
    "fundcraft_personverification": {"identifier": "last_name", "joins": "JOIN django.fundcraft_person p ON p.id = t.person_id", "client_filter": "p.owner_client_id"},

    # VIA closingprocess -> fcos -> fund -> company -> client
    "fundcraft_closingprocess": {"identifier": "closing_code", "joins": "JOIN django.fundcraft_fundclassofshares fcos ON fcos.id = t.fund_class_of_shares_id JOIN django.fundcraft_fund f ON f.id = fcos.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_closingprocessdocumentsrelationship": {"identifier": "id", "joins": "JOIN django.fundcraft_closingprocess cp ON cp.id = t.closing_process_id JOIN django.fundcraft_fundclassofshares fcos ON fcos.id = cp.fund_class_of_shares_id JOIN django.fundcraft_fund f ON f.id = fcos.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_closingprocessshare": {"identifier": "share_name", "joins": "JOIN django.fundcraft_closingprocess cp ON cp.id = t.closing_process_id JOIN django.fundcraft_fundclassofshares fcos ON fcos.id = cp.fund_class_of_shares_id JOIN django.fundcraft_fund f ON f.id = fcos.fund_id JOIN django.fundcraft_company co ON co.id = f.company_id", "client_filter": "co.owner_client_id"},

    # VIA document (polymorphic entity)
    "fundcraft_document": {"identifier": "name", "joins": "LEFT JOIN django.fundcraft_company co ON co.uuid = t.entity_uuid LEFT JOIN django.fundcraft_investor inv ON inv.uuid = t.entity_uuid LEFT JOIN django.fundcraft_person p ON p.uuid = t.entity_uuid", "client_filter": "COALESCE(co.owner_client_id, inv.owner_client_id, p.owner_client_id)"},

    # VIA bankaccount -> company -> client
    "fundcraft_bankaccount": {"identifier": "iban", "joins": "JOIN django.fundcraft_company co ON co.uuid = t.entity_uuid", "client_filter": "co.owner_client_id"},
    "fundcraft_bankaccountbalance": {"identifier": "id", "joins": "JOIN django.fundcraft_bankaccount ba ON ba.uuid = t.bank_account_id JOIN django.fundcraft_company co ON co.uuid = ba.entity_uuid", "client_filter": "co.owner_client_id"},

    # VIA asset -> investment -> client
    "fundcraft_asset": {"identifier": "asset_name", "joins": "JOIN django.fundcraft_investment inv ON inv.uuid = t.investment_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_equityasset": {"identifier": "internal_code", "joins": "JOIN django.fundcraft_asset a ON a.id = t.asset_ptr_id JOIN django.fundcraft_investment inv ON inv.uuid = a.investment_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_debtasset": {"identifier": "internal_code", "joins": "JOIN django.fundcraft_asset a ON a.id = t.asset_ptr_id JOIN django.fundcraft_investment inv ON inv.uuid = a.investment_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_convertibleasset": {"identifier": "internal_code", "joins": "JOIN django.fundcraft_asset a ON a.id = t.asset_ptr_id JOIN django.fundcraft_investment inv ON inv.uuid = a.investment_id", "client_filter": "inv.owner_client_id"},
    "fundcraft_safeasset": {"identifier": "internal_code", "joins": "JOIN django.fundcraft_asset a ON a.id = t.asset_ptr_id JOIN django.fundcraft_investment inv ON inv.uuid = a.investment_id", "client_filter": "inv.owner_client_id"},

    # VIA investmentprocess -> company -> client
    "fundcraft_investmentprocess": {"identifier": "name_holding", "joins": "JOIN django.fundcraft_company co ON co.id = t.target_company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_investmentprocess_v2": {"identifier": "investment_alias", "joins": "JOIN django.fundcraft_company co ON co.id = t.target_company_id", "client_filter": "co.owner_client_id"},
    "fundcraft_investmentprocessdocumentsrelationship": {"identifier": "id", "joins": "JOIN django.fundcraft_investmentprocess ip ON ip.id = t.investment_process_id JOIN django.fundcraft_company co ON co.id = ip.target_company_id", "client_filter": "co.owner_client_id"},

    # VIA divestmentprocess -> company -> client
    "fundcraft_divestmentprocess": {"identifier": "id", "joins": "JOIN django.fundcraft_company co ON co.id = t.portfolio_company_id", "client_filter": "co.owner_client_id"},

    # TABLES WITHOUT CLIENT JOIN PATH (identifier only, empty joins/filter)
    "fundcraft_accountinginstruction": {"identifier": "payment_reference_code", "joins": "", "client_filter": ""},
    "fundcraft_accountinginstructionpayments": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_activityriskprocess": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_agendapoint": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_agendapointlog": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_amlglobalriskassessment": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_annualaccountcheck": {"identifier": "title", "joins": "", "client_filter": ""},
    "fundcraft_annualaccountcheckcomment": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_answer": {"identifier": "content", "joins": "", "client_filter": ""},
    "fundcraft_apirequestlog": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_approval": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_assetgroupvaluation": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_assettransaction": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_assistantrelationship": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_bankaccountholder": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_capitalcallequalisation": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_capitalcallexcludablefromequalisation": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_capitalcallfeelinefundclassofshares": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_capitalcallinvestment": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_capitalcallline": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_capitalcallshareholderaccinstexternalpayment": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_capitalcallshareholderequalisationline": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_capitalcallshareholderhistory": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_capitalcallshareholderjointaccount": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_capitalcallshareholderline": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_capitalcallshareholderotherline": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_comment": {"identifier": "content", "joins": "", "client_filter": ""},
    "fundcraft_committee": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_committeehtml": {"identifier": "hash_code", "joins": "", "client_filter": ""},
    "fundcraft_committeeparticipant": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_committeetypeparticipant": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_companydocumentrequestlog": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_companydocumentsrequestlog": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_companyexternaldocumentrequestlog": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_companyexternaldocumentsession": {"identifier": "provider_code", "joins": "", "client_filter": ""},
    "fundcraft_companyexternaldocumentsrequestlog": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_convertibleassetgroupvaluation": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_convertibleassetownership": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_convertibletranche": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_convertibletrancheincome": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_countryriskprocess": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_debtassetgroupvaluation": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_debtcollateral": {"identifier": "description", "joins": "", "client_filter": ""},
    "fundcraft_distributionline": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_distributionshareholderhistory": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_distributionshareholderline": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_distributionshareholderpayment": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_divestmentconvertibleasset": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_divestmentequityasset": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_divestmentprocess_assets": {"identifier": "asset_name", "joins": "", "client_filter": ""},
    "fundcraft_divestmentprocess_proceeds": {"identifier": "asset_name", "joins": "", "client_filter": ""},
    "fundcraft_documentsession": {"identifier": "provider_code", "joins": "", "client_filter": ""},
    "fundcraft_documentsourcelog": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_emailmessage": {"identifier": "subject", "joins": "", "client_filter": ""},
    "fundcraft_emailthread": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_employee": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_entity": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_entity_history": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_entityscreeninghitongoingmonitoring": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_equityassetgroupvaluation": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_equityassetownership": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_equityassetseller": {"identifier": "ai_status_code", "joins": "", "client_filter": ""},
    "fundcraft_fcprocesschecklist": {"identifier": "description", "joins": "", "client_filter": ""},
    "fundcraft_fcprocessmeetingassistants": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_fcprocessmeetings": {"identifier": "title", "joins": "", "client_filter": ""},
    "fundcraft_fctaskexecution": {"identifier": "codename", "joins": "", "client_filter": ""},
    "fundcraft_four_eyes_comment": {"identifier": "comment", "joins": "", "client_filter": ""},
    "fundcraft_foureyespolicy": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_fundclassofsharescapitalcall": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_governingprocess": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_incomingemail": {"identifier": "email_id", "joins": "", "client_filter": ""},
    "fundcraft_internalnote": {"identifier": "content", "joins": "", "client_filter": ""},
    "fundcraft_internalnotementionedemployee": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_investmentprocess_assets": {"identifier": "asset_name", "joins": "", "client_filter": ""},
    "fundcraft_investmentprocesscommitteeresolution": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_investordocumentsrelationship": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_investorfunddetaildocumentsrelationship": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_investorfunddetailjointaccount": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_investorsubscriptionbanckaccountinformation": {"identifier": "bank_name", "joins": "", "client_filter": ""},
    "fundcraft_investorsubscriptionjointaccount": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_investorsubscriptionline": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_investorsubscriptionnominee": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kyc_document_type_master_process_relation": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kyc_document_type_master_variant": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kyc_screeninghitsession": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_kyc_screeningtargetsession": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_kycamlanswer": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kycamlquestion": {"identifier": "code", "joins": "", "client_filter": ""},
    "fundcraft_kycamlquestionoption": {"identifier": "text", "joins": "", "client_filter": ""},
    "fundcraft_kycamlquestionquestionoption": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kyccompliancereview": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kycdocumenttargetssession": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_kycdrawing": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kycduediligenceparticipantsdocuments": {"identifier": "code", "joins": "", "client_filter": ""},
    "fundcraft_kycescalationform": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kycgencomment": {"identifier": "comment", "joins": "", "client_filter": ""},
    "fundcraft_kychistoricdump": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kycindividualamlassessment": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kycindividualamlchoice": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kycparticipant": {"identifier": "category", "joins": "", "client_filter": ""},
    "fundcraft_kycparticipantrelationship": {"identifier": "relation_type", "joins": "", "client_filter": ""},
    "fundcraft_kycparticipantscreeninghit": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kycparticipantstructureentity": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kycprocesscomment": {"identifier": "content", "joins": "", "client_filter": ""},
    "fundcraft_kycprocessparticipant": {"identifier": "participant_category", "joins": "", "client_filter": ""},
    "fundcraft_kycprocessreview": {"identifier": "review_role", "joins": "", "client_filter": ""},
    "fundcraft_kycrcpfsreview": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kycrequestchangereview": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kycsarstrfiling": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_kyctargetcompany": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kyctargetcompanyamlassessment": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kyctargetcompanyamlchoice": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kyctargetperson": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kyctransaction": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_kycverificationsession": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_lpportalinvestoraccount": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_mitigationmeasures": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_mitigationmeasurescheck": {"identifier": "title", "joins": "", "client_filter": ""},
    "fundcraft_mitigationmeasurescheckcomment": {"identifier": "comment", "joins": "", "client_filter": ""},
    "fundcraft_notificationcontact": {"identifier": "email", "joins": "", "client_filter": ""},
    "fundcraft_notificationcontact_distributionlisttype_through": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_notificationstatus": {"identifier": "status_code", "joins": "", "client_filter": ""},
    "fundcraft_onlinedocumentation": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_outgoingemail": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_parallelfundgroup": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_paymentissuesresolutionmove": {"identifier": "move_name", "joins": "", "client_filter": ""},
    "fundcraft_paymentissuesresolutionprocessescalation": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_pepmaterialityassessment": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_pepmaterialitychoice": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_pepstatus": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_pmqualitativepolicyrule": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_pmqualitativepolicyruleresult": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_pmreview": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_question": {"identifier": "content", "joins": "", "client_filter": ""},
    "fundcraft_reclassofsharesline": {"identifier": "reference", "joins": "", "client_filter": ""},
    "fundcraft_rmevaluation": {"identifier": "code", "joins": "", "client_filter": ""},
    "fundcraft_rmqualitativepolicyrule": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_rmqualitativepolicyruleresult": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_rmreview": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_safeassetownership": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_screeningadversemedia": {"identifier": "title", "joins": "", "client_filter": ""},
    "fundcraft_screeningadversemediaassessment": {"identifier": "assessment", "joins": "", "client_filter": ""},
    "fundcraft_screeninghit": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_screeninghit_backup": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_screeninghitassessment": {"identifier": "assessment", "joins": "", "client_filter": ""},
    "fundcraft_screeninghitrequestlog": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_screeningongoingmonitoringactivity": {"identifier": "entity_name", "joins": "", "client_filter": ""},
    "fundcraft_screeningrequestlog": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_screeningsongoingmonitoringcheck": {"identifier": "error_code", "joins": "", "client_filter": ""},
    "fundcraft_sessionrequestlog": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_sessionrequestlogsession": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_structurecontractualrelationship": {"identifier": "contractual_relationship_type", "joins": "", "client_filter": ""},
    "fundcraft_structureentityparticipants": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_structurerelation": {"identifier": "relation_type", "joins": "", "client_filter": ""},
    "fundcraft_tag": {"identifier": "type", "joins": "", "client_filter": ""},
    "fundcraft_task": {"identifier": "title", "joins": "", "client_filter": ""},
    "fundcraft_tranche": {"identifier": "tranche_name", "joins": "", "client_filter": ""},
    "fundcraft_trancheactiondrivenfee": {"identifier": "reference_fee_type", "joins": "", "client_filter": ""},
    "fundcraft_trancheactiondrivenfeeratchet": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_tranchedrawdown": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_tranchefinancialcovenant": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_tranchefixinterest": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_trancheprincipalrepayment": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_tranchevariableinterest": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_transferdetail": {"identifier": "ai_status_code", "joins": "", "client_filter": ""},
    "fundcraft_transferofshareline": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_ubo": {"identifier": "ubo_type", "joins": "", "client_filter": ""},
    "fundcraft_underlyingclassofshares": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_underlyingclosing": {"identifier": "transaction_code", "joins": "", "client_filter": ""},
    "fundcraft_underlyingdistribution": {"identifier": "transaction_code", "joins": "", "client_filter": ""},
    "fundcraft_underlyingdrawdown": {"identifier": "transaction_code", "joins": "", "client_filter": ""},
    "fundcraft_underlyingfundcas": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_underlyingfundtransaction": {"identifier": "transaction_code", "joins": "", "client_filter": ""},
    "fundcraft_underlyinginvestment": {"identifier": "target_investment_name", "joins": "", "client_filter": ""},
    "fundcraft_underlyingportfolio": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_underlyingtotal": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_underlyingtotalgroupvaluation": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_valuationportfolioasset": {"identifier": "asset_name", "joins": "", "client_filter": ""},
    "fundcraft_variant_document_type": {"identifier": "code", "joins": "", "client_filter": ""},
    "fundcraft_vehicletyperiskprocess": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_verificationrequestlog": {"identifier": "status", "joins": "", "client_filter": ""},
    "fundcraft_verificationsession": {"identifier": "code", "joins": "", "client_filter": ""},
    "fundcraft_verificationsessioncommunication": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_version": {"identifier": "version", "joins": "", "client_filter": ""},
    "fundcraft_versionuser": {"identifier": "user_email", "joins": "", "client_filter": ""},
    "fundcraft_watchlist_subscription": {"identifier": "id", "joins": "", "client_filter": ""},
    "fundcraft_workflow": {"identifier": "workflow_title", "joins": "", "client_filter": ""},
    "fundcraft_workflowstep": {"identifier": "name", "joins": "", "client_filter": ""},
    "fundcraft_workflowtransition": {"identifier": "id", "joins": "", "client_filter": ""},
    "integrations_gmailcredential": {"identifier": "email", "joins": "", "client_filter": ""},
    "integrations_imapsconfig": {"identifier": "username", "joins": "", "client_filter": ""},
    "messaging_emailmessagedocumentsrelationship": {"identifier": "id", "joins": "", "client_filter": ""},
}


def build_client_filtered_query(table: str, client_uuid: str | None = None, select_cols: str = "t.*") -> str:
    """
    Build a query for a table with optional client UUID filtering.

    Args:
        table: Table name (without schema prefix)
        client_uuid: Optional client UUID to filter by
        select_cols: Columns to select (default: "t.*")

    Returns:
        SQL query string

    Example:
        >>> query = build_client_filtered_query("fundcraft_fund", "abc-123-uuid")
        >>> print(query)
        SELECT t.*
        FROM django.fundcraft_fund t
        JOIN django.fundcraft_company co ON co.id = t.company_id
        WHERE co.owner_client_id = 'abc-123-uuid'
    """
    config = TABLE_CONFIG.get(table)

    if config is None:
        # Table not in mapping - return simple query without client filter
        query = f"SELECT {select_cols} FROM django.{table} t"
        if client_uuid:
            # Can't filter by client - warn in comment
            query = f"-- WARNING: No client join path for {table}\n{query}"
        return query

    joins = config["joins"]
    client_filter = config["client_filter"]

    query = f"SELECT {select_cols}\nFROM django.{table} t"

    if joins:
        query += f"\n{joins}"

    if client_uuid and client_filter:
        query += f"\nWHERE {client_filter} = '{client_uuid}'"

    return query

# Tables list derived from TABLE_CONFIG (sorted for consistent fzf display)
TABLES = sorted(TABLE_CONFIG.keys())


def select_table_with_fzf(tables):
    """Use fzf to select a table."""
    tables_text = "\n".join(tables)
    try:
        result = subprocess.run(
            ['fzf', '--height=40%', '--reverse', '--border', '--prompt=Select table: ', '--query=fundcraft_'],
            input=tables_text,
            text=True,
            capture_output=True
        )
        if result.returncode != 0:
            print("No table selected", file=sys.stderr)
            sys.exit(0)
        return result.stdout.strip()
    except FileNotFoundError:
        print("Error: fzf not found", file=sys.stderr)
        sys.exit(1)


def get_random_uuids(table, limit=200, client_uuid=None):
    """Get random UUIDs with identifier column from the table using psql.

    Args:
        table: Table name (without schema prefix)
        limit: Maximum number of UUIDs to return
        client_uuid: Optional client UUID to filter results by
    """
    # Get config for this table
    config = TABLE_CONFIG.get(table, {})
    identifier_col = config.get("identifier", "id")
    joins = config.get("joins", "")
    client_filter = config.get("client_filter", "")

    # Build query with optional client filter
    if client_uuid and client_filter:
        query = f"""
            SELECT t.uuid, t.{identifier_col}
            FROM django.{table} t
            {joins}
            WHERE {client_filter} = '{client_uuid}'
            ORDER BY RANDOM()
            LIMIT {limit};
        """
    elif client_uuid and not client_filter:
        # Table has no client join path - show warning and return unfiltered
        print(f"Warning: No client join path for {table}, showing all records", file=sys.stderr)
        query = f"SELECT uuid, {identifier_col} FROM django.{table} ORDER BY RANDOM() LIMIT {limit};"
    else:
        # No client filter - return random records
        query = f"SELECT uuid, {identifier_col} FROM django.{table} ORDER BY RANDOM() LIMIT {limit};"

    try:
        result = subprocess.run(
            ['psql', DB_URL, '-t', '-c', query],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse UUID and identifier from output
        # Format: "uuid | identifier"
        rows = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    uuid_val = parts[0]
                    identifier_val = parts[1] if parts[1] else '(no identifier)'
                    # Replace newlines with spaces so fzf can filter properly
                    identifier_val = identifier_val.replace('\n', ' ').replace('\r', ' ')
                    rows.append((uuid_val, identifier_val))
        return rows
    except subprocess.CalledProcessError as e:
        print(f"Error querying database: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: psql not found", file=sys.stderr)
        sys.exit(1)


def select_uuid_with_fzf(uuid_rows, table):
    """Use fzf to select a UUID."""
    if not uuid_rows:
        print(f"No UUIDs found in table {table}", file=sys.stderr)
        sys.exit(1)

    # Format for display: "uuid - identifier"
    display_lines = [f"{uuid} - {identifier}" for uuid, identifier in uuid_rows]
    display_text = "\n".join(display_lines)

    try:
        result = subprocess.run(
            ['fzf', '--height=40%', '--reverse', '--border', f'--prompt=Select UUID from {table}: '],
            input=display_text,
            text=True,
            capture_output=True
        )
        if result.returncode != 0:
            print("No UUID selected", file=sys.stderr)
            sys.exit(0)

        # Extract just the UUID (before the " - ")
        selected = result.stdout.strip()
        uuid = selected.split(' - ')[0]
        return uuid
    except FileNotFoundError:
        print("Error: fzf not found", file=sys.stderr)
        sys.exit(1)


def get_client_uuid_from_args():
    """Parse --client argument from command line."""
    import argparse
    parser = argparse.ArgumentParser(description="Interactive UUID selector for Fundcraft database tables.")
    parser.add_argument(
        '--client', '-c',
        type=str,
        help='Filter results by client UUID (e.g., nJr4WoFWwrc5D2HUaMszqf for Moonfare)'
    )
    args = parser.parse_args()
    return args.client


def main():
    """Interactive UUID selector for Fundcraft database tables."""
    # Parse arguments
    client_uuid = get_client_uuid_from_args()

    if client_uuid:
        print(f"Filtering by client: {client_uuid}", file=sys.stderr)

    # Select table
    table = select_table_with_fzf(TABLES)

    # Get random UUIDs with identifiers (filtered by client if provided)
    uuid_rows = get_random_uuids(table, client_uuid=client_uuid)

    # Select UUID
    selected_uuid = select_uuid_with_fzf(uuid_rows, table)

    # Output the selected UUID (only thing going to stdout)
    print(selected_uuid)


if __name__ == '__main__':
    main()
