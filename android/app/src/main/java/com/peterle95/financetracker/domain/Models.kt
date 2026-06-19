package com.peterle95.financetracker.domain

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import java.time.LocalDate

enum class TransactionType(val label: String) {
    Expense("Expense"),
    Income("Income");

    companion object {
        fun fromLabel(value: String): TransactionType =
            entries.firstOrNull { it.label.equals(value, ignoreCase = true) } ?: Expense
    }
}

data class FinanceTransaction(
    val uiKey: String,
    val exportId: String?,
    val type: TransactionType,
    val date: String,
    val amount: Double,
    val category: String,
    val description: String,
    val behaviorDate: String?,
)

data class CategoryState(
    val expenses: List<String> = CategoryDefaults.expense,
    val incomes: List<String> = CategoryDefaults.income,
) {
    fun forType(type: TransactionType): List<String> =
        if (type == TransactionType.Expense) expenses else incomes
}

data class FinanceTotals(
    val income: Double,
    val expenses: Double,
    val net: Double,
    val fixedCosts: Double,
    val baseIncome: Double,
    val flexibleExpenses: Double,
    val flexibleIncome: Double,
)

data class TransactionCounts(
    val flexibleExpenses: Int,
    val flexibleIncomes: Int,
)

data class InsightsSummary(
    val months: List<String>,
    val totals: FinanceTotals,
    val expenseCategories: Map<String, Double>,
    val incomeCategories: Map<String, Double>,
    val transactionCounts: TransactionCounts,
)

data class DashboardSummary(
    val currentMonth: String,
    val income: Double,
    val expenses: Double,
    val net: Double,
    val topExpenseCategories: List<Pair<String, Double>>,
    val balanceEstimate: Double?,
    val remainingDailyBudget: Double = 0.0,
)

data class IncomeSource(
    val key: String = "",
    val amount: Double = 0.0,
    val description: String = "Base Income",
    val startDate: String = "2000-01-01",
    val endDate: String? = null,
    val extraJson: JsonObject = buildJsonObject {},
)

data class FixedCost(
    val key: String = "",
    val amount: Double = 0.0,
    val description: String = "",
    val startDate: String = "2000-01-01",
    val endDate: String? = null,
    val extraJson: JsonObject = buildJsonObject {},
)

data class CategoryBudgets(
    val expense: Map<String, Double> = emptyMap(),
    val income: Map<String, Double> = emptyMap(),
    val extraJson: JsonObject = buildJsonObject {},
) {
    companion object {
        fun fromJson(json: JsonObject?): CategoryBudgets =
            CategoryBudgets(
                expense = json?.get(TransactionType.Expense.label).numberMapOrEmpty(),
                income = json?.get(TransactionType.Income.label).numberMapOrEmpty(),
                extraJson = JsonObject(
                    json?.filterKeys {
                        it != TransactionType.Expense.label && it != TransactionType.Income.label
                    } ?: emptyMap(),
                ),
            )
    }
}

data class AssetBalances(
    val bankAccount: Double = 0.0,
    val wallet: Double = 0.0,
    val savings: Double = 0.0,
    val investments: Double = 0.0,
    val moneyLent: Double = 0.0,
    val hasAnyBalanceField: Boolean = false,
) {
    val netWorth: Double
        get() = bankAccount + wallet + savings + investments + moneyLent
}

data class Loan(
    val key: String = "",
    val id: String = "",
    val borrower: String = "",
    val amount: Double = 0.0,
    val description: String = "",
    val date: String = "",
    val extraJson: JsonObject = buildJsonObject {},
)

data class AssetSnapshot(
    val key: String = "",
    val date: String,
    val bankBalance: Double = 0.0,
    val walletBalance: Double = 0.0,
    val savingsBalance: Double = 0.0,
    val investmentBalance: Double = 0.0,
    val moneyLentBalance: Double = 0.0,
    val note: String = "",
    val netWorth: Double = bankBalance + walletBalance + savingsBalance + investmentBalance + moneyLentBalance,
    val extraJson: JsonObject = buildJsonObject {},
)

data class BudgetReportDay(
    val date: String,
    val target: Double,
    val spent: Double,
    val dailyDelta: Double,
    val cumulativeFlexibleBalance: Double,
    val status: String,
)

data class BudgetReport(
    val month: String,
    val monthLabel: String,
    val baseMonthlyIncome: Double,
    val fixedCosts: Double,
    val dailySavingsGoal: Double,
    val monthlySavingsGoal: Double,
    val netMonthlyFlexibleBudget: Double,
    val initialDailySpendingTarget: Double,
    val flexibleIncomeThisMonth: Double,
    val totalIncome: Double,
    val carryoverAmount: Double,
    val includeNegativeCarryover: Boolean,
    val remainingFlexibleBudget: Double,
    val remainingDays: Int,
    val adjustedDailyTarget: Double,
    val days: List<BudgetReportDay>,
    val statusTitle: String,
    val statusDetail: String,
    val textReport: String,
) {
    companion object {
        fun invalid(month: String, message: String) = BudgetReport(
            month = month,
            monthLabel = month,
            baseMonthlyIncome = 0.0,
            fixedCosts = 0.0,
            dailySavingsGoal = 0.0,
            monthlySavingsGoal = 0.0,
            netMonthlyFlexibleBudget = 0.0,
            initialDailySpendingTarget = 0.0,
            flexibleIncomeThisMonth = 0.0,
            totalIncome = 0.0,
            carryoverAmount = 0.0,
            includeNegativeCarryover = false,
            remainingFlexibleBudget = 0.0,
            remainingDays = 0,
            adjustedDailyTarget = 0.0,
            days = emptyList(),
            statusTitle = "Invalid month",
            statusDetail = message,
            textReport = message,
        )
    }
}

data class NetWorthChange(
    val months: Int,
    val current: Double,
    val past: Double,
    val change: Double,
    val changePercent: Double,
    val pastDate: String,
)

data class AssetAllocation(
    val label: String,
    val value: Double,
    val percent: Double,
)

data class NetWorthSummary(
    val currentNetWorth: Double,
    val balances: AssetBalances,
    val changes: Map<Int, NetWorthChange?>,
    val snapshots: List<AssetSnapshot>,
    val allocation: List<AssetAllocation>,
    val reportText: String,
)

data class BudgetSettings(
    val monthlyIncome: List<IncomeSource> = emptyList(),
    val monthlyIncomeWasLegacyNumber: Boolean = false,
    val fixedCosts: List<FixedCost> = emptyList(),
    val balances: AssetBalances = AssetBalances(),
    val dailySavingsGoal: Double = 0.0,
    val categoryBudgets: CategoryBudgets = CategoryBudgets(),
    val loans: List<Loan> = emptyList(),
    val assetSnapshots: List<AssetSnapshot> = emptyList(),
    val extraJson: JsonObject = buildJsonObject {},
) {
    fun toJsonObjectPreserving(raw: JsonObject = buildJsonObject {}): JsonObject =
        buildJsonObject {
            raw.forEach { (key, value) ->
                if (key !in budgetSettingsKeys) put(key, value)
            }
            extraJson.forEach { (key, value) ->
                if (key !in budgetSettingsKeys) put(key, value)
            }
            put("monthly_income", JsonArray(monthlyIncome.map { it.toJsonObject() }))
            put("fixed_costs", JsonArray(fixedCosts.map { it.toJsonObject() }))
            put("bank_account_balance", balances.bankAccount)
            put("wallet_balance", balances.wallet)
            put("savings_balance", balances.savings)
            put("investment_balance", balances.investments)
            put("money_lent_balance", balances.moneyLent)
            put("daily_savings_goal", dailySavingsGoal)
            put("category_budgets", categoryBudgets.toJsonObject(raw["category_budgets"] as? JsonObject))
            put("loans", JsonArray(loans.map { it.toJsonObject() }))
            put("asset_snapshots", JsonArray(assetSnapshots.map { it.toJsonObject() }))
        }

    companion object {
        fun fromJson(json: JsonObject): BudgetSettings {
            val monthlyElement = json["monthly_income"]
            val legacyIncome = monthlyElement?.jsonPrimitiveOrNull()?.doubleOrNull
            val monthlyIncome = when {
                legacyIncome != null -> {
                    if (legacyIncome > 0.0) {
                        listOf(
                            IncomeSource(
                                key = stableKey("income", 0, legacyIncome, "Base Income", "2000-01-01", null),
                                amount = legacyIncome,
                                description = "Base Income",
                                startDate = "2000-01-01",
                                endDate = null,
                            ),
                        )
                    } else {
                        emptyList()
                    }
                }

                monthlyElement is JsonArray -> monthlyElement.mapNotNullIndexed { index, element ->
                    (element as? JsonObject)?.toIncomeSource(index)
                }

                else -> emptyList()
            }

            val fixedCosts = (json["fixed_costs"] as? JsonArray)
                ?.mapNotNullIndexed { index, element -> (element as? JsonObject)?.toFixedCost(index) }
                ?: emptyList()

            val balanceKeys = listOf(
                "bank_account_balance",
                "wallet_balance",
                "savings_balance",
                "investment_balance",
                "money_lent_balance",
            )

            val snapshots = (json["asset_snapshots"] as? JsonArray)
                ?.mapNotNullIndexed { index, element -> (element as? JsonObject)?.toAssetSnapshot(index) }
                ?.sortedBy { it.date }
                ?: emptyList()
            val loans = (json["loans"] as? JsonArray)
                ?.mapNotNullIndexed { index, element -> (element as? JsonObject)?.toLoan(index) }
                ?: emptyList()

            return BudgetSettings(
                monthlyIncome = monthlyIncome,
                monthlyIncomeWasLegacyNumber = legacyIncome != null,
                fixedCosts = fixedCosts,
                balances = AssetBalances(
                    bankAccount = json.numberValue("bank_account_balance"),
                    wallet = json.numberValue("wallet_balance"),
                    savings = json.numberValue("savings_balance"),
                    investments = json.numberValue("investment_balance"),
                    moneyLent = json.numberValue("money_lent_balance"),
                    hasAnyBalanceField = balanceKeys.any { json.containsKey(it) },
                ),
                dailySavingsGoal = json.numberValue("daily_savings_goal"),
                categoryBudgets = CategoryBudgets.fromJson(json["category_budgets"] as? JsonObject),
                loans = loans,
                assetSnapshots = snapshots,
                extraJson = JsonObject(json.filterKeys { it !in budgetSettingsKeys }),
            )
        }

        private val budgetSettingsKeys = setOf(
            "monthly_income",
            "fixed_costs",
            "bank_account_balance",
            "wallet_balance",
            "savings_balance",
            "investment_balance",
            "money_lent_balance",
            "daily_savings_goal",
            "category_budgets",
            "loans",
            "asset_snapshots",
        )
    }
}

fun todayIsoDate(): String = LocalDate.now().toString()

private val incomeSourceKeys = setOf("amount", "description", "start_date", "end_date")
private val fixedCostKeys = setOf("amount", "description", "desc", "start_date", "end_date")
private val loanKeys = setOf("id", "borrower", "amount", "description", "date")
private val assetSnapshotKeys = setOf(
    "date",
    "bank_balance",
    "wallet_balance",
    "savings_balance",
    "investment_balance",
    "money_lent_balance",
    "note",
    "net_worth",
)

private fun JsonObject.toIncomeSource(index: Int): IncomeSource {
    val amount = numberValue("amount")
    val description = stringValue("description") ?: "Base Income"
    val startDate = stringValue("start_date") ?: "2000-01-01"
    val endDate = nullableStringValue("end_date")
    return IncomeSource(
        key = stableKey("income", index, amount, description, startDate, endDate),
        amount = amount,
        description = description,
        startDate = startDate,
        endDate = endDate,
        extraJson = JsonObject(filterKeys { it !in incomeSourceKeys }),
    )
}

private fun JsonObject.toFixedCost(index: Int): FixedCost {
    val amount = numberValue("amount")
    val description = stringValue("description") ?: stringValue("desc") ?: "Untitled"
    val startDate = stringValue("start_date") ?: "2000-01-01"
    val endDate = nullableStringValue("end_date")
    return FixedCost(
        key = stableKey("fixed", index, amount, description, startDate, endDate),
        amount = amount,
        description = description,
        startDate = startDate,
        endDate = endDate,
        extraJson = JsonObject(filterKeys { it !in fixedCostKeys }),
    )
}

private fun JsonObject.toLoan(index: Int): Loan {
    val amount = numberValue("amount")
    val borrower = stringValue("borrower") ?: ""
    val description = stringValue("description") ?: ""
    val date = stringValue("date") ?: ""
    val id = stringValue("id") ?: stableKey("loan", index, amount, borrower, date, description)
    return Loan(
        key = id,
        id = id,
        borrower = borrower,
        amount = amount,
        description = description,
        date = date,
        extraJson = JsonObject(filterKeys { it !in loanKeys }),
    )
}

private fun JsonObject.toAssetSnapshot(index: Int): AssetSnapshot {
    val bank = numberValue("bank_balance")
    val wallet = numberValue("wallet_balance")
    val savings = numberValue("savings_balance")
    val investments = numberValue("investment_balance")
    val moneyLent = numberValue("money_lent_balance")
    val date = stringValue("date") ?: ""
    val note = stringValue("note") ?: ""
    val calculatedNetWorth = bank + wallet + savings + investments + moneyLent
    return AssetSnapshot(
        key = stableKey("snapshot", index, calculatedNetWorth, date, note, null),
        date = date,
        bankBalance = bank,
        walletBalance = wallet,
        savingsBalance = savings,
        investmentBalance = investments,
        moneyLentBalance = moneyLent,
        note = note,
        netWorth = this["net_worth"]?.jsonPrimitiveOrNull()?.doubleOrNull ?: calculatedNetWorth,
        extraJson = JsonObject(filterKeys { it !in assetSnapshotKeys }),
    )
}

private fun IncomeSource.toJsonObject(): JsonObject =
    buildJsonObject {
        extraJson.forEach { (key, value) ->
            if (key !in incomeSourceKeys) put(key, value)
        }
        put("amount", amount)
        put("description", description)
        put("start_date", startDate)
        putNullableString("end_date", endDate)
    }

private fun FixedCost.toJsonObject(): JsonObject =
    buildJsonObject {
        extraJson.forEach { (key, value) ->
            if (key !in fixedCostKeys) put(key, value)
        }
        put("amount", amount)
        put("desc", description)
        put("start_date", startDate)
        putNullableString("end_date", endDate)
    }

private fun Loan.toJsonObject(): JsonObject =
    buildJsonObject {
        extraJson.forEach { (key, value) ->
            if (key !in loanKeys) put(key, value)
        }
        put("id", id)
        put("borrower", borrower)
        put("amount", amount)
        put("description", description)
        put("date", date)
    }

private fun AssetSnapshot.toJsonObject(): JsonObject =
    buildJsonObject {
        extraJson.forEach { (key, value) ->
            if (key !in assetSnapshotKeys) put(key, value)
        }
        put("date", date)
        put("bank_balance", bankBalance)
        put("wallet_balance", walletBalance)
        put("savings_balance", savingsBalance)
        put("investment_balance", investmentBalance)
        put("money_lent_balance", moneyLentBalance)
        put("note", note)
        put("net_worth", netWorth)
    }

private fun CategoryBudgets.toJsonObject(raw: JsonObject?): JsonObject =
    buildJsonObject {
        raw?.forEach { (key, value) ->
            if (key != TransactionType.Expense.label && key != TransactionType.Income.label) put(key, value)
        }
        extraJson.forEach { (key, value) ->
            if (key != TransactionType.Expense.label && key != TransactionType.Income.label) put(key, value)
        }
        put(TransactionType.Expense.label, expense.toJsonObject())
        put(TransactionType.Income.label, income.toJsonObject())
    }

private fun Map<String, Double>.toJsonObject(): JsonObject =
    buildJsonObject {
        entries.sortedBy { it.key.lowercase() }.forEach { (key, value) ->
            put(key, value)
        }
    }

private fun JsonElement?.numberMapOrEmpty(): Map<String, Double> =
    runCatching {
        this?.jsonObject?.mapValues { (_, value) ->
            value.jsonPrimitiveOrNull()?.doubleOrNull ?: 0.0
        }.orEmpty()
    }.getOrDefault(emptyMap())

private fun JsonObject.numberValue(key: String): Double =
    this[key]?.jsonPrimitiveOrNull()?.doubleOrNull ?: 0.0

private fun JsonObject.stringValue(key: String): String? =
    nullableStringValue(key)?.takeIf { it.isNotBlank() }

private fun JsonObject.nullableStringValue(key: String): String? =
    this[key].stringOrNull()

private fun JsonElement?.stringOrNull(): String? =
    if (this == null || this is JsonNull) null else jsonPrimitiveOrNull()?.contentOrNull

private fun JsonElement.jsonPrimitiveOrNull() =
    runCatching { jsonPrimitive }.getOrNull()

private fun JsonObjectBuilderShim.putNullableString(key: String, value: String?) {
    if (value == null) {
        put(key, JsonNull)
    } else {
        put(key, value)
    }
}

private typealias JsonObjectBuilderShim = kotlinx.serialization.json.JsonObjectBuilder

private fun stableKey(
    prefix: String,
    index: Int,
    amount: Double,
    description: String,
    startDate: String,
    endDate: String?,
): String = "$prefix:$index:${amount.toBits()}:${description.hashCode()}:${startDate.hashCode()}:${endDate.hashCode()}"

private inline fun <T, R : Any> Iterable<T>.mapNotNullIndexed(transform: (Int, T) -> R?): List<R> {
    val destination = ArrayList<R>()
    forEachIndexed { index, item ->
        transform(index, item)?.let(destination::add)
    }
    return destination
}
