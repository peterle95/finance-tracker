package com.peterle95.financetracker.data

import com.peterle95.financetracker.domain.Loan
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Test

class FinanceDirectoryStoreTest {
    @Test
    fun migrationReconstructsNormalizedLegacyAndPreservesUnknownData() = runBlocking {
        val legacy = """
            {
              "expenses": [{
                "date": "2026-08-01", "amount": 12, "category": "Café Bar",
                "description": "Lunch", "behavior_date": "2026-07-31", "receipt": "kept"
              }],
              "incomes": [{
                "id": "income-1", "date": "2026-08-01", "amount": 1000,
                "category": "Salary", "description": "Pay"
              }],
              "categories": {"Expense": ["Café Bar"], "Income": ["Salary"]},
              "budget_settings": {"daily_savings_goal": 4, "custom_setting": {"kept": true}},
              "custom_root": {"kept": true}
            }
        """.trimIndent()
        val directory = InMemoryFinanceDirectory(mutableMapOf("finance_data.json" to legacy))

        val result = FinanceDirectoryStore(directory).reload()

        assertTrue(result.migratedLegacy)
        assertEquals(legacy, directory.files.getValue("finance_data.json"))
        assertTrue(directory.files.containsKey("transactions_expense_cafe-bar.json"))
        val expense = result.document.records.first { it.transaction.type == TransactionType.Expense }
        assertNotNull(expense.transaction.exportId)
        assertEquals("2026-07-31", expense.transaction.behaviorDate)
        assertEquals("kept", expense.extraJson["receipt"]!!.jsonPrimitive.content)
        assertEquals(true, result.document.topLevelExtra["custom_root"]!!.jsonObject["kept"]!!.jsonPrimitive.content.toBoolean())
        assertEquals(
            true,
            result.document.budgetSettings["custom_setting"]!!.jsonObject["kept"]!!.jsonPrimitive.content.toBoolean(),
        )
        assertEquals("income-1", result.document.records.first { it.transaction.type == TransactionType.Income }.transaction.exportId)
    }

    @Test
    fun categoriesCreateDeleteRenameAndBlockUnsafeDeletion() = runBlocking {
        val directory = migratedDirectory()
        val store = FinanceDirectoryStore(directory)
        store.reload()
        directory.clearOperations()

        store.setCategories(TransactionType.Expense, listOf("Food", "Travel", "Fóód"))
        assertTrue(directory.files.containsKey("transactions_expense_food-2.json"))
        assertFalse(directory.writes.contains("transactions_expense_food.json"))

        store.setCategories(TransactionType.Expense, listOf("Food", "Travel"))
        assertFalse(directory.files.containsKey("transactions_expense_food-2.json"))

        expectFailure("Cannot delete category with transactions: Food") {
            store.setCategories(TransactionType.Expense, listOf("Travel"))
        }
        store.setCategories(TransactionType.Expense, listOf("Dining", "Travel"))
        val categories = directory.element("categories.json").jsonObject
        assertEquals("food", categories["Expense"]!!.jsonArray[0].jsonObject["file_key"]!!.jsonPrimitive.content)
        assertEquals("Dining", directory.element("transactions_expense_food.json").jsonArray.single().jsonObject["category"]!!.jsonPrimitive.content)
        val expenseBudgets = directory.element("budget.json").jsonObject["category_budgets"]!!
            .jsonObject["Expense"]!!.jsonObject
        assertEquals(25.0, expenseBudgets["Dining"]!!.jsonPrimitive.content.toDouble(), 0.0)
        assertFalse(expenseBudgets.containsKey("Food"))

        expectFailure("Cannot delete category with transactions: Dining") {
            store.setCategories(TransactionType.Expense, listOf("Travel", "Cafe"))
        }
        assertFalse(directory.files.containsKey("transactions_expense_cafe.json"))
        assertEquals(listOf("Salary", "Gift"), store.document.value.categories.incomes)
    }

    @Test
    fun transactionChangesTouchOnlyOwnersAndPreserveIdsAndExternalRows() = runBlocking {
        val directory = migratedDirectory()
        val store = FinanceDirectoryStore(directory)
        store.reload()
        directory.clearOperations()

        store.addTransaction(TransactionType.Expense, "2026-08-03", 5.0, "Food", "Coffee", null)
        assertEquals(listOf("transactions_expense_food.json"), directory.writes)
        val addedId = directory.element("transactions_expense_food.json").jsonArray
            .last().jsonObject["id"]!!.jsonPrimitive.content

        directory.append("transactions_expense_food.json", transaction("external", "Food", "External"))
        directory.clearOperations()
        store.updateTransaction(
            addedId,
            TransactionType.Expense,
            "2026-08-04",
            7.0,
            "Travel",
            "Moved",
            "2026-08-02",
        )

        assertEquals(
            listOf("transactions_expense_travel.json", "transactions_expense_food.json"),
            directory.writes,
        )
        assertTrue(directory.element("transactions_expense_food.json").jsonArray.any { it.jsonObject["id"]?.jsonPrimitive?.content == "external" })
        val moved = directory.element("transactions_expense_travel.json").jsonArray.single().jsonObject
        assertEquals(addedId, moved["id"]!!.jsonPrimitive.content)
        assertEquals("2026-08-02", moved["behavior_date"]!!.jsonPrimitive.content)

        directory.clearOperations()
        store.deleteTransaction(addedId)
        assertEquals(listOf("transactions_expense_travel.json"), directory.writes)
        assertTrue(directory.element("transactions_expense_travel.json").jsonArray.isEmpty())
        assertTrue(directory.element("transactions_expense_food.json").jsonArray.any { it.jsonObject["id"]?.jsonPrimitive?.content == "external" })
    }

    @Test
    fun ownerMutationRereadsLatestFilesAndLoanMutationWritesBothOwners() = runBlocking {
        val directory = migratedDirectory()
        val store = FinanceDirectoryStore(directory)
        store.reload()
        directory.append("transactions_income_gift.json", transaction("external-income", "Gift", "External"))
        directory.files["loans.json"] = """[{"id":"external-loan","borrower":"E","amount":3,"description":"X","date":"2026-08-01"}]"""
        val netWorth = directory.element("net_worth.json").jsonObject.toMutableMap()
        netWorth["bank_account_balance"] = JsonPrimitive(999)
        netWorth["money_lent_balance"] = JsonPrimitive(3)
        netWorth["external"] = JsonPrimitive("kept")
        directory.files["net_worth.json"] = Json.encodeToString(JsonObject.serializer(), JsonObject(netWorth))
        val budgetBefore = directory.files.getValue("budget.json")
        directory.clearOperations()

        store.mutateOwner(FileOwner.Loans) {
            FinanceJsonCodec.addLoan(it, Loan(id = "android-loan", borrower = "A", amount = 7.0, description = "Lunch"))
        }

        assertEquals(listOf("loans.json", "net_worth.json"), directory.writes)
        assertEquals(budgetBefore, directory.files.getValue("budget.json"))
        assertEquals(2, directory.element("loans.json").jsonArray.size)
        val writtenNetWorth = directory.element("net_worth.json").jsonObject
        assertEquals(999.0, writtenNetWorth["bank_account_balance"]!!.jsonPrimitive.content.toDouble(), 0.0)
        assertEquals(10.0, writtenNetWorth["money_lent_balance"]!!.jsonPrimitive.content.toDouble(), 0.0)
        assertEquals("kept", writtenNetWorth["external"]!!.jsonPrimitive.content)
        assertTrue(directory.element("transactions_income_gift.json").jsonArray.any {
            it.jsonObject["id"]?.jsonPrimitive?.content == "external-income"
        })

        directory.clearOperations()
        store.mutateOwner(FileOwner.Loans) {
            FinanceJsonCodec.updateLoan(
                it,
                "android-loan",
                Loan(borrower = "A2", amount = 9.0, description = "Updated"),
            )
        }
        assertEquals(listOf("loans.json", "net_worth.json"), directory.writes)
        assertEquals(12.0, directory.element("net_worth.json").jsonObject["money_lent_balance"]!!.jsonPrimitive.content.toDouble(), 0.0)
        assertEquals("android-loan", directory.element("loans.json").jsonArray[1].jsonObject["id"]!!.jsonPrimitive.content)

        directory.clearOperations()
        store.mutateOwner(FileOwner.Loans) { FinanceJsonCodec.returnLoan(it, "android-loan") }
        assertEquals(listOf("loans.json", "net_worth.json"), directory.writes)
        assertEquals(3.0, directory.element("net_worth.json").jsonObject["money_lent_balance"]!!.jsonPrimitive.content.toDouble(), 0.0)
        assertEquals("external-loan", directory.element("loans.json").jsonArray.single().jsonObject["id"]!!.jsonPrimitive.content)
    }

    @Test
    fun reloadCreatesMissingRegisteredTransactionAndReportsUnsafeDirectoryProblems() = runBlocking {
        val directory = migratedDirectory()
        val store = FinanceDirectoryStore(directory)
        store.reload()
        directory.files.remove("transactions_expense_travel.json")
        directory.files["budget.sync-conflict-20260810.json"] = "{}"
        directory.files["transactions_expense_orphan.json"] = "[]"
        directory.clearOperations()

        val result = store.reload()

        assertEquals("[]", directory.files["transactions_expense_travel.json"]?.filterNot(Char::isWhitespace))
        assertEquals(listOf("transactions_expense_travel.json"), directory.writes)
        assertTrue(result.warnings.any { "conflict" in it.lowercase() })
        assertTrue(result.warnings.any { "orphan" in it.lowercase() })

        directory.files.remove("budget.json")
        expectFailure("budget.json is missing or is not a JSON object.") { store.reload() }

        val partial = InMemoryFinanceDirectory(mutableMapOf("loans.json" to "[]"))
        expectFailure("categories.json is missing") { FinanceDirectoryStore(partial).reload() }

        val duplicate = migratedDirectory()
        duplicate.files["categories.json"] = """{"Expense":[{"name":"Food","file_key":"food"},{"name":"food","file_key":"food-2"}],"Income":[]}"""
        expectFailure("Duplicate Expense category name") { FinanceDirectoryStore(duplicate).reload() }
    }

    private suspend fun migratedDirectory(): InMemoryFinanceDirectory {
        val legacy = """
            {
              "expenses": [{"id":"food-1","date":"2026-08-01","amount":3,"category":"Food","description":"Snack","extra":"kept"}],
              "incomes": [],
              "categories": {"Expense":["Food","Travel"],"Income":["Salary","Gift"]},
              "budget_settings": {
                "money_lent_balance":0,"bank_account_balance":1,
                "category_budgets":{"Expense":{"Food":25},"Income":{}}
              }
            }
        """.trimIndent()
        return InMemoryFinanceDirectory(mutableMapOf("finance_data.json" to legacy)).also {
            FinanceDirectoryStore(it).reload()
            it.clearOperations()
        }
    }

    private fun transaction(id: String, category: String, description: String) = JsonObject(
        mapOf(
            "id" to JsonPrimitive(id),
            "date" to JsonPrimitive("2026-08-02"),
            "amount" to JsonPrimitive(4),
            "category" to JsonPrimitive(category),
            "description" to JsonPrimitive(description),
        ),
    )

    private suspend fun expectFailure(message: String, block: suspend () -> Unit) {
        try {
            block()
            fail("Expected failure containing: $message")
        } catch (error: Throwable) {
            assertTrue("Expected <$message>, got <${error.message}>", error.message.orEmpty().contains(message))
        }
    }

    private class InMemoryFinanceDirectory(
        val files: MutableMap<String, String> = mutableMapOf(),
    ) : FinanceDirectory {
        val writes = mutableListOf<String>()
        val deletes = mutableListOf<String>()

        override suspend fun listFiles() = files.keys.toList()
        override suspend fun readText(name: String) = files[name]
        override suspend fun writeText(name: String, content: String) {
            writes += name
            files[name] = content
        }

        override suspend fun delete(name: String) {
            deletes += name
            files.remove(name)
        }

        fun clearOperations() {
            writes.clear()
            deletes.clear()
        }

        fun element(name: String) = Json.parseToJsonElement(files.getValue(name))

        fun append(name: String, value: JsonObject) {
            val rows = element(name).jsonArray.toMutableList()
            rows += value
            files[name] = Json.encodeToString(JsonArray.serializer(), JsonArray(rows))
        }
    }
}
