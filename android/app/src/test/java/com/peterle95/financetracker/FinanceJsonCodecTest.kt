package com.peterle95.financetracker

import com.peterle95.financetracker.data.FinanceJsonCodec
import com.peterle95.financetracker.data.FinanceJsonFileStore
import com.peterle95.financetracker.domain.AssetBalances
import com.peterle95.financetracker.domain.CategoryDefaults
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class FinanceJsonCodecTest {
    @Test
    fun loadingJsonDocumentFromTextAppliesDefaultsAndPreservesFields() {
        val document = FinanceJsonCodec.parse(sampleJson)

        assertEquals(2, document.transactions.size)
        val expense = document.transactions.first { it.type == TransactionType.Expense }
        assertNull(expense.exportId)
        assertEquals("2026-06-09", expense.behaviorDate)
        assertEquals(CategoryDefaults.expense, document.categories.expenses)
        assertEquals(42.0, document.budgetSettings["bank_account_balance"]!!.jsonPrimitive.content.toDouble(), 0.0)
        assertTrue(document.topLevelExtra.containsKey("unexpected_root"))
        assertTrue(document.records.first().extraJson.containsKey("note"))
    }

    @Test
    fun addingTransactionPreservesUnknownFieldsAndBudgetSettings() {
        val document = FinanceJsonCodec.parse(sampleJson)
        val updated = FinanceJsonCodec.addTransaction(
            document = document,
            type = TransactionType.Expense,
            date = "2026-06-12",
            amount = 8.25,
            category = "Food",
            description = "Coffee",
            id = "android-uuid",
        )
        val root = Json.parseToJsonElement(FinanceJsonCodec.encode(updated)).jsonObject

        assertEquals("root", root["unexpected_root"]!!.jsonPrimitive.content)
        assertEquals(42.0, root["budget_settings"]!!.jsonObject["bank_account_balance"]!!.jsonPrimitive.content.toDouble(), 0.0)
        assertEquals("kept", root["expenses"]!!.jsonArray[0].jsonObject["note"]!!.jsonPrimitive.content)
        val added = root["expenses"]!!.jsonArray[1].jsonObject
        assertEquals("android-uuid", added["id"]!!.jsonPrimitive.content)
        assertEquals("2026-06-12", added["date"]!!.jsonPrimitive.content)
        assertFalse(added.containsKey("behavior_date"))
    }

    @Test
    fun addingBnplTransactionWritesBehaviorDateAndPreservesUnknownFields() {
        val document = FinanceJsonCodec.parse(sampleJson)
        val updated = FinanceJsonCodec.addTransaction(
            document = document,
            type = TransactionType.Expense,
            date = "2026-07-01",
            amount = 48.0,
            category = "Shopping",
            description = "Pay next month",
            behaviorDate = "2026-06-16",
            id = "android-bnpl",
        )
        val root = Json.parseToJsonElement(FinanceJsonCodec.encode(updated)).jsonObject
        val added = root["expenses"]!!.jsonArray[1].jsonObject

        assertEquals("root", root["unexpected_root"]!!.jsonPrimitive.content)
        assertEquals("kept", root["expenses"]!!.jsonArray[0].jsonObject["note"]!!.jsonPrimitive.content)
        assertEquals("2026-07-01", added["date"]!!.jsonPrimitive.content)
        assertEquals("2026-06-16", added["behavior_date"]!!.jsonPrimitive.content)
    }

    @Test
    fun deletingTransactionUsesExportedId() {
        val document = FinanceJsonCodec.parse(sampleJson)
        val updated = FinanceJsonCodec.deleteTransactionByExportId(document, "income-1")
        val root = Json.parseToJsonElement(FinanceJsonCodec.encode(updated)).jsonObject

        assertEquals(0, root["incomes"]!!.jsonArray.size)
        assertEquals(1, root["expenses"]!!.jsonArray.size)
    }

    @Test
    fun editingCategoriesWritesThemBackToJson() {
        val document = FinanceJsonCodec.parse(sampleJson)
        val updated = FinanceJsonCodec.updateCategories(
            document = document,
            type = TransactionType.Expense,
            categories = listOf("Groceries", "Travel", "Groceries"),
        )
        val root = Json.parseToJsonElement(FinanceJsonCodec.encode(updated)).jsonObject
        val categories = root["categories"]!!.jsonObject["Expense"]!!.jsonArray.map { it.jsonPrimitive.content }

        assertEquals(listOf("Groceries", "Travel"), categories)
    }

    @Test
    fun typedBudgetSettingsReadLegacyMonthlyIncome() {
        val document = FinanceJsonCodec.parse(
            """
            {
              "expenses": [],
              "incomes": [],
              "budget_settings": {
                "monthly_income": 1234,
                "fixed_costs": []
              },
              "categories": {}
            }
            """.trimIndent(),
        )

        assertEquals(1234.0, document.budgetSettingsModel.monthlyIncome.single().amount, 0.0)
        assertEquals("Base Income", document.budgetSettingsModel.monthlyIncome.single().description)
    }

    @Test
    fun budgetMutationPreservesDesktopOnlyFieldsAndUnknownNestedFields() {
        val document = FinanceJsonCodec.parse(budgetSettingsJson)
        val updated = FinanceJsonCodec.updateBalances(
            document,
            AssetBalances(
                bankAccount = 10.0,
                wallet = 20.0,
                savings = 30.0,
                investments = 40.0,
                moneyLent = 50.0,
                hasAnyBalanceField = true,
            ),
        )
        val root = Json.parseToJsonElement(FinanceJsonCodec.encode(updated)).jsonObject
        val budget = root["budget_settings"]!!.jsonObject

        assertEquals("root", root["unexpected_root"]!!.jsonPrimitive.content)
        assertEquals("keep-me", budget["desktop_only"]!!.jsonPrimitive.content)
        assertTrue(budget["ai_settings"]!!.jsonObject.containsKey("api_key"))
        assertEquals("monthly", budget["fixed_costs"]!!.jsonArray[0].jsonObject["cadence"]!!.jsonPrimitive.content)
        assertEquals("kept", root["expenses"]!!.jsonArray[0].jsonObject["note"]!!.jsonPrimitive.content)
        assertEquals(10.0, budget["bank_account_balance"]!!.jsonPrimitive.content.toDouble(), 0.0)
    }

    @Test
    fun updatingRecurringBudgetRowsPreservesUnknownRowFields() {
        val document = FinanceJsonCodec.parse(budgetSettingsJson)
        val income = document.budgetSettingsModel.monthlyIncome.single()
        val fixedCost = document.budgetSettingsModel.fixedCosts.single()
        val updatedIncome = FinanceJsonCodec.updateIncomeSource(
            document,
            income.key,
            income.copy(amount = 2600.0, description = "Updated Salary"),
        )
        val updatedCost = FinanceJsonCodec.updateFixedCost(
            updatedIncome,
            fixedCost.key,
            fixedCost.copy(amount = 950.0, description = "Updated Rent"),
        )
        val budget = Json.parseToJsonElement(FinanceJsonCodec.encode(updatedCost))
            .jsonObject["budget_settings"]!!
            .jsonObject

        assertEquals(
            "kept",
            budget["monthly_income"]!!.jsonArray[0].jsonObject["payroll_id"]!!.jsonPrimitive.content,
        )
        assertEquals(
            "monthly",
            budget["fixed_costs"]!!.jsonArray[0].jsonObject["cadence"]!!.jsonPrimitive.content,
        )
    }

    @Test
    fun recordAssetSnapshotWritesDesktopCompatibleShape() {
        val document = FinanceJsonCodec.parse(budgetSettingsJson)
        val updated = FinanceJsonCodec.recordAssetSnapshot(document, "2026-06-18", "Android")
        val snapshot = Json.parseToJsonElement(FinanceJsonCodec.encode(updated))
            .jsonObject["budget_settings"]!!
            .jsonObject["asset_snapshots"]!!
            .jsonArray
            .last()
            .jsonObject

        assertEquals("2026-06-18", snapshot["date"]!!.jsonPrimitive.content)
        assertEquals("Android", snapshot["note"]!!.jsonPrimitive.content)
        assertTrue(snapshot.containsKey("bank_balance"))
        assertTrue(snapshot.containsKey("wallet_balance"))
        assertTrue(snapshot.containsKey("savings_balance"))
        assertTrue(snapshot.containsKey("investment_balance"))
        assertTrue(snapshot.containsKey("money_lent_balance"))
        assertTrue(snapshot.containsKey("net_worth"))
    }

    @Test
    fun fileStoreReloadsLatestText() = runBlocking {
        var fileText = sampleJson
        val store = FinanceJsonFileStore(
            readText = { fileText },
            writeText = { fileText = it },
        )

        store.reload()
        assertEquals(2, store.document.value.transactions.size)

        fileText = FinanceJsonCodec.encode(
            FinanceJsonCodec.addTransaction(
                FinanceJsonCodec.parse(fileText),
                TransactionType.Income,
                "2026-06-20",
                20.0,
                "Gift",
                "Syncthing update",
                id = "desktop-change",
            ),
        )
        store.reload()

        assertEquals(3, store.document.value.transactions.size)
        assertTrue(store.document.value.transactions.any { it.exportId == "desktop-change" })
    }

    private val sampleJson = """
        {
          "expenses": [
            {
              "date": "2026-06-10",
              "amount": 12.5,
              "category": "Food",
              "description": "Lunch",
              "behavior_date": "2026-06-09",
              "note": "kept"
            }
          ],
          "incomes": [
            {
              "id": "income-1",
              "date": "2026-06-01",
              "amount": 1000,
              "category": "Salary",
              "description": "Pay"
            }
          ],
          "budget_settings": { "bank_account_balance": 42 },
          "unexpected_root": "root"
        }
    """.trimIndent()

    private val budgetSettingsJson = """
        {
          "expenses": [
            {
              "date": "2026-06-10",
              "amount": 12.5,
              "category": "Food",
              "description": "Lunch",
              "note": "kept"
            }
          ],
          "incomes": [],
          "budget_settings": {
            "monthly_income": [
              {
                "amount": 2500,
                "description": "Salary",
                "start_date": "2026-01-01",
                "end_date": null,
                "payroll_id": "kept"
              }
            ],
            "fixed_costs": [
              {
                "amount": 900,
                "desc": "Rent",
                "start_date": "2026-01-01",
                "end_date": null,
                "cadence": "monthly"
              }
            ],
            "bank_account_balance": 1,
            "wallet_balance": 2,
            "savings_balance": 3,
            "investment_balance": 4,
            "money_lent_balance": 5,
            "daily_savings_goal": 10,
            "category_budgets": {
              "Expense": { "Food": 40 },
              "Income": {},
              "Custom": { "kept": true }
            },
            "asset_snapshots": [],
            "ai_settings": { "api_key": "secret" },
            "desktop_only": "keep-me"
          },
          "unexpected_root": "root"
        }
    """.trimIndent()
}
