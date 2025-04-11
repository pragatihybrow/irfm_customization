# import frappe
# from frappe.query_builder.functions import CombineDatetime, Sum
# from frappe.utils import nowtime, today

# def custom_get_available_batches(kwargs):
#     stock_ledger_entry = frappe.qb.DocType("Stock Ledger Entry")
#     batch_ledger = frappe.qb.DocType("Serial and Batch Entry")
#     batch_table = frappe.qb.DocType("Batch")

#     query = (
#         frappe.qb.from_(stock_ledger_entry)
#         .inner_join(batch_ledger).on(stock_ledger_entry.serial_and_batch_bundle == batch_ledger.parent)
#         .inner_join(batch_table).on(batch_ledger.batch_no == batch_table.name)
#         .select(
#             batch_ledger.batch_no,
#             batch_ledger.warehouse,
#             Sum(batch_ledger.qty).as_("qty"),
#             stock_ledger_entry.pack_size,
#             stock_ledger_entry.name,
#         )
#         .where(
#             (batch_table.disabled == 0)
#             & ((batch_table.expiry_date >= today()) | (batch_table.expiry_date.isnull()))
#             & (stock_ledger_entry.is_cancelled == 0)
#         )
#         .groupby(batch_ledger.batch_no, batch_ledger.warehouse)
#     )

#     # Date/time filtering
#     if kwargs.get("posting_date"):
#         if not kwargs.get("posting_time"):
#             kwargs["posting_time"] = nowtime()

#         query = query.where(
#             CombineDatetime(stock_ledger_entry.posting_date, stock_ledger_entry.posting_time)
#             <= CombineDatetime(kwargs["posting_date"], kwargs["posting_time"])
#         )

#     # Filter by fields like warehouse and item_code
#     for field in ["warehouse", "item_code"]:
#         if val := kwargs.get(field):
#             query = query.where(stock_ledger_entry[field].isin(val) if isinstance(val, list) else stock_ledger_entry[field] == val)

#     # Optional batch number filtering
#     if batch_nos := kwargs.get("batch_no"):
#         query = query.where(batch_ledger.batch_no.isin(batch_nos) if isinstance(batch_nos, list) else batch_ledger.batch_no == batch_nos)

#     # Order by strategy
#     order_by = batch_table.creation
#     if kwargs.get("based_on") == "LIFO":
#         query = query.orderby(order_by, order=frappe.qb.desc)
#     elif kwargs.get("based_on") == "Expiry":
#         order_by = batch_table.expiry_date
#         query = query.orderby(order_by)
#     else:  # default FIFO
#         query = query.orderby(order_by)

#     # Ignore specific vouchers if needed
#     if ignore_vouchers := kwargs.get("ignore_voucher_nos"):
#         query = query.where(stock_ledger_entry.voucher_no.notin(ignore_vouchers))

#     return query.run(as_dict=True)



# def custom_get_available_batches(kwargs):
#     stock_ledger_entry = frappe.qb.DocType("Stock Ledger Entry")
#     batch_ledger = frappe.qb.DocType("Serial and Batch Entry")
#     batch_table = frappe.qb.DocType("Batch")

#     query = (
#         frappe.qb.from_(stock_ledger_entry)
#         .inner_join(batch_ledger).on(stock_ledger_entry.serial_and_batch_bundle == batch_ledger.parent)
#         .inner_join(batch_table).on(batch_ledger.batch_no == batch_table.name)
#         .select(
#             batch_ledger.batch_no,
#             batch_ledger.warehouse,
#             Sum(batch_ledger.qty).as_("qty"),
#             stock_ledger_entry.pack_size,
#             stock_ledger_entry.name,
#         )
#         .where(
#             (batch_table.disabled == 0)
#             & ((batch_table.expiry_date >= today()) | (batch_table.expiry_date.isnull()))
#             & (stock_ledger_entry.is_cancelled == 0)
#         )
#         .groupby(batch_ledger.batch_no, batch_ledger.warehouse)
#     )

#     # Date/time filtering
#     if kwargs.get("posting_date"):
#         if not kwargs.get("posting_time"):
#             kwargs["posting_time"] = nowtime()

#         query = query.where(
#             CombineDatetime(stock_ledger_entry.posting_date, stock_ledger_entry.posting_time)
#             <= CombineDatetime(kwargs["posting_date"], kwargs["posting_time"])
#         )

#     # Filter by fields like warehouse and item_code
#     for field in ["warehouse", "item_code"]:
#         if val := kwargs.get(field):
#             query = query.where(stock_ledger_entry[field].isin(val) if isinstance(val, list) else stock_ledger_entry[field] == val)

#     # Optional batch number filtering
#     if batch_nos := kwargs.get("batch_no"):
#         query = query.where(batch_ledger.batch_no.isin(batch_nos) if isinstance(batch_nos, list) else batch_ledger.batch_no == batch_nos)

#     # Order by strategy
#     order_by = batch_table.creation
#     if kwargs.get("based_on") == "LIFO":
#         query = query.orderby(order_by, order=frappe.qb.desc)
#     elif kwargs.get("based_on") == "Expiry":
#         order_by = batch_table.expiry_date
#         query = query.orderby(order_by)
#     else:  # default FIFO
#         query = query.orderby(order_by)

#     # Ignore specific vouchers if needed
#     if ignore_vouchers := kwargs.get("ignore_voucher_nos"):
#         query = query.where(stock_ledger_entry.voucher_no.notin(ignore_vouchers))

#     return query.run(as_dict=True)


import frappe
from frappe.query_builder.functions import CombineDatetime, Sum
from frappe.utils import nowtime, today

def custom_get_available_batches(kwargs):
    stock_ledger_entry = frappe.qb.DocType("Stock Ledger Entry")
    batch_ledger = frappe.qb.DocType("Serial and Batch Entry")
    batch_table = frappe.qb.DocType("Batch")

    query = (
        frappe.qb.from_(stock_ledger_entry)
        .inner_join(batch_ledger).on(stock_ledger_entry.serial_and_batch_bundle == batch_ledger.parent)
        .inner_join(batch_table).on(batch_ledger.batch_no == batch_table.name)
        .select(
            stock_ledger_entry.item_code,
            batch_ledger.warehouse,
            batch_ledger.batch_no,
            Sum(batch_ledger.qty).as_("qty"),
        )
        .where(
            (stock_ledger_entry.is_cancelled == 0) &
            (batch_table.disabled == 0) &
            ((batch_table.expiry_date >= today()) | (batch_table.expiry_date.isnull()))
        )
        .groupby(batch_ledger.batch_no, batch_ledger.warehouse, stock_ledger_entry.item_code)
    )

    # Date/time filtering
    if kwargs.get("posting_date"):
        if not kwargs.get("posting_time"):
            kwargs["posting_time"] = nowtime()

        query = query.where(
            CombineDatetime(stock_ledger_entry.posting_date, stock_ledger_entry.posting_time)
            <= CombineDatetime(kwargs["posting_date"], kwargs["posting_time"])
        )

    # Filter by warehouse and item_code
    for field in ["warehouse", "item_code"]:
        if val := kwargs.get(field):
            query = query.where(
                stock_ledger_entry[field].isin(val) if isinstance(val, list) else stock_ledger_entry[field] == val
            )

    # Filter specific batches if passed
    if batch_nos := kwargs.get("batch_no"):
        query = query.where(
            batch_ledger.batch_no.isin(batch_nos) if isinstance(batch_nos, list) else batch_ledger.batch_no == batch_nos
        )

    # Sorting strategy
    order_by = batch_table.creation
    if kwargs.get("based_on") == "LIFO":
        query = query.orderby(order_by, order=frappe.qb.desc)
    elif kwargs.get("based_on") == "Expiry":
        query = query.orderby(batch_table.expiry_date)
    else:  # Default FIFO
        query = query.orderby(order_by)

    # Ignore specific vouchers
    if ignore_vouchers := kwargs.get("ignore_voucher_nos"):
        query = query.where(stock_ledger_entry.voucher_no.notin(ignore_vouchers))

    # Debug log
    print(">>> custom_get_available_batches kwargs:", kwargs)
    result = query.run(as_dict=True)
    print(">>> Result:", result)

    return result
