package com.peterle95.financetracker.data

import com.peterle95.financetracker.domain.Loan
import com.peterle95.financetracker.domain.SavingsGoal
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.delay
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
import kotlin.system.measureNanoTime

class FinanceDirectoryStoreTest {
    @Test
    fun reloadReadsEachLiveFileOnce() = runBlocking {
        val directory = performanceDirectory()
        val result = FinanceDirectoryStore(directory).reload()

        assertEquals(60, result.document.transactions.size)
        assertEquals(66, directory.reads.size)
        assertEquals(66, directory.reads.distinct().size)
        assertEquals(1, directory.listings)
        assertTrue(directory.writes.isEmpty())
    }

    @Test
    fun ordinarySavesReadOnlyTheirOwnersAndPublishExternalRows() = runBlocking {
        val directory = performanceDirectory()
        val store = FinanceDirectoryStore(directory)
        store.reload()
        val owner = "transactions_expense_category-60.json"
        directory.append(owner, transaction("external", "Category 60", "External"))
        directory.clearOperations()

        store.addTransaction(TransactionType.Expense, "2026-10-04", 5.0, "Category 60", "Added", null, "added")
        assertEquals(listOf("categories.json", owner, owner), directory.reads)
        assertEquals(1, directory.listings)
        assertEquals(62, store.document.value.records.size)
        assertTrue(store.document.value.transactions.any { it.exportId == "external" })

        directory.clearOperations()
        store.updateTransaction("added", TransactionType.Expense, "2026-10-04", 7.0, "Category 60", "Updated", null)
        assertEquals(listOf("categories.json", owner, owner), directory.reads)
        assertEquals(7.0, store.document.value.transactions.first { it.exportId == "added" }.amount, 0.0)

        directory.clearOperations()
        store.deleteTransaction("added")
        assertEquals(listOf("categories.json", owner, owner), directory.reads)
        assertEquals(61, store.document.value.records.size)

        directory.files["budget.json"] = """{"daily_savings_goal":2,"monthly_income":[{"amount":9,"description":"External","custom":true}],"unknown":"kept"}"""
        directory.clearOperations()
        store.mutateOwner(FileOwner.Budget) { FinanceJsonCodec.setDailySavingsGoal(it, 12.0) }
        assertEquals(listOf("budget.json", "budget.json"), directory.reads)
        assertEquals(listOf("budget.json"), directory.writes)
        assertEquals(1, directory.listings)
        assertEquals(12.0, store.document.value.budgetSettingsModel.dailySavingsGoal, 0.0)
        assertEquals(9.0, store.document.value.budgetSettingsModel.monthlyIncome.single().amount, 0.0)
        assertEquals("kept", store.document.value.budgetSettings["unknown"]!!.jsonPrimitive.content)
    }

    @Test
    fun externallyMovedTransactionIsFoundWithoutLeavingACachedDuplicate() = runBlocking {
        val directory = migratedDirectory()
        val store = FinanceDirectoryStore(directory)
        store.reload()
        directory.files["transactions_expense_travel.json"] = directory.files.getValue("transactions_expense_food.json")
        directory.files["transactions_expense_food.json"] = "[]"

        store.updateTransaction("food-1", TransactionType.Expense, "2026-10-04", 6.0, "Travel", "Updated", null)

        val record = store.document.value.records.single()
        assertEquals("Travel", record.transaction.category)
        assertEquals("food-1", record.transaction.exportId)
        assertEquals("kept", record.extraJson["extra"]!!.jsonPrimitive.content)
        assertEquals(store.document.value, store.reload().document)
    }

    @Test
    fun addingToAnExternallyMovedDestinationReplacesTheCachedSource() = runBlocking {
        val directory = migratedDirectory()
        val store = FinanceDirectoryStore(directory)
        store.reload()
        directory.files["transactions_expense_travel.json"] = directory.files.getValue("transactions_expense_food.json")
        directory.files["transactions_expense_food.json"] = "[]"

        store.addTransaction(TransactionType.Expense, "2026-10-04", 5.0, "Travel", "Added", null)

        assertEquals(2, store.document.value.transactions.size)
        assertEquals("Travel", store.document.value.transactions.single { it.exportId == "food-1" }.category)
        assertEquals(store.document.value, store.reload().document)
    }

    @Test
    fun newlyReadExternalRowsReceivePersistedIdsBeforePublication() = runBlocking {
        val directory = migratedDirectory()
        val store = FinanceDirectoryStore(directory)
        store.reload()
        val owner = "transactions_expense_food.json"
        directory.append(owner, JsonObject(transaction("external", "Food", "External") - "id"))

        store.addTransaction(TransactionType.Expense, "2026-10-04", 5.0, "Food", "Added", null)

        val externalId = store.document.value.transactions.single { it.description == "External" }.exportId
        assertNotNull(externalId)
        assertEquals(externalId, directory.element(owner).jsonArray[1].jsonObject["id"]!!.jsonPrimitive.content)
        store.deleteTransaction(externalId!!)
        assertFalse(store.document.value.transactions.any { it.description == "External" })
    }

    @Test
    fun failedVerificationAndReloadKeepLastGoodDocument() = runBlocking {
        val directory = migratedDirectory()
        val store = FinanceDirectoryStore(directory)
        val lastGood = store.reload().document
        directory.corruptWrites = true

        expectFailure("did not verify") {
            store.addTransaction(TransactionType.Expense, "2026-10-04", 5.0, "Food", "Failed", null)
        }
        assertEquals(lastGood, store.document.value)
        directory.files["budget.json"] = "[]"
        expectFailure("budget.json is missing or is not a JSON object.") { store.reload() }
        assertEquals(lastGood, store.document.value)
    }

    @Test
    fun savingsAllocationUsesLatestBalanceAndExternalGoals() = runBlocking {
        val directory = migratedDirectory()
        val store = FinanceDirectoryStore(directory)
        store.reload()
        store.mutateOwner(FileOwner.SavingsGoals) {
            FinanceJsonCodec.addSavingsGoal(it, SavingsGoal(name = "Target", targetAmount = 100.0))
        }
        val key = store.document.value.budgetSettingsModel.savingsGoals.single().key
        directory.files["net_worth.json"] = """{"savings_balance":10}"""
        directory.append("savings_goals.json", Json.parseToJsonElement("""{"name":"External","target_amount":20,"allocated_amount":8,"custom":true}""").jsonObject)
        directory.clearOperations()

        expectFailure("Insufficient savings") {
            store.mutateOwner(FileOwner.SavingsGoals) { FinanceJsonCodec.allocateSavingsGoal(it, key, 3.0) }
        }
        assertTrue(directory.writes.isEmpty())
        directory.clearOperations()
        store.mutateOwner(FileOwner.SavingsGoals) { FinanceJsonCodec.allocateSavingsGoal(it, key, 2.0) }
        assertEquals(listOf("savings_goals.json", "net_worth.json", "savings_goals.json"), directory.reads)
        assertEquals(2, store.document.value.budgetSettingsModel.savingsGoals.size)
        assertEquals(10.0, store.document.value.budgetSettingsModel.balances.savings, 0.0)
        assertEquals(store.document.value, store.reload().document)
    }

    @Test
    fun syntheticLatencyProbe() = runBlocking {
        val directory = performanceDirectory()
        directory.delayMillis = System.getenv("FINANCE_TEST_IO_DELAY_MS")?.toLong() ?: 0L
        val store = FinanceDirectoryStore(directory)
        suspend fun measure(label: String, action: suspend () -> Unit) {
            directory.clearOperations()
            val elapsed = measureNanoTime { action(); store.warnings() } / 1_000_000
            println("$label: delay=${directory.delayMillis}ms reads=${directory.reads.size} listings=${directory.listings} writes=${directory.writes.size} elapsed=${elapsed}ms")
        }
        measure("cold reload") { store.reload() }
        measure("warm reload") { store.reload() }
        measure("add") { store.addTransaction(TransactionType.Expense, "2026-10-04", 5.0, "Category 60", "Added", null, "probe") }
        measure("update") { store.updateTransaction("probe", TransactionType.Expense, "2026-10-04", 7.0, "Category 60", "Updated", null) }
        measure("delete") { store.deleteTransaction("probe") }
        measure("budget") { store.mutateOwner(FileOwner.Budget) { FinanceJsonCodec.setDailySavingsGoal(it, 12.0) } }
        assertEquals(60, store.document.value.transactions.size)
        assertEquals(12.0, store.document.value.budgetSettingsModel.dailySavingsGoal, 0.0)
    }

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
        assertEquals(store.document.value, store.reload().document)
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
        assertEquals(5, directory.reads.size)
        assertEquals(setOf("categories.json", "transactions_expense_food.json", "transactions_expense_travel.json"), directory.reads.toSet())
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
        assertEquals(listOf("loans.json", "net_worth.json", "loans.json", "net_worth.json"), directory.reads)
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
        assertTrue(store.reload().document.transactions.any { it.exportId == "external-income" })
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

    private fun performanceDirectory(): InMemoryFinanceDirectory {
        val categories = (1..60).joinToString(",") { """{"name":"Category $it","file_key":"category-$it"}""" }
        val files = mutableMapOf(
            "categories.json" to """{"Expense":[$categories],"Income":[]}""",
            "budget.json" to "{}",
            "net_worth.json" to "{}",
            "preferences.json" to "{}",
            "loans.json" to "[]",
            "savings_goals.json" to "[]",
        )
        (1..60).forEach {
            files["transactions_expense_category-$it.json"] = JsonArray(listOf(transaction("id-$it", "Category $it", "Existing"))).toString()
        }
        return InMemoryFinanceDirectory(files)
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
        val reads = mutableListOf<String>()
        var listings = 0
        var corruptWrites = false
        var delayMillis = 0L

        override suspend fun listFiles(): List<String> {
            listings++
            delay(delayMillis)
            return files.keys.toList()
        }

        override suspend fun readText(name: String): String? {
            reads += name
            delay(delayMillis)
            return files[name]
        }
        override suspend fun writeText(name: String, content: String) {
            writes += name
            delay(delayMillis)
            files[name] = if (corruptWrites) "{}" else content
        }

        override suspend fun delete(name: String) {
            deletes += name
            files.remove(name)
        }

        fun clearOperations() {
            writes.clear()
            deletes.clear()
            reads.clear()
            listings = 0
        }

        fun element(name: String) = Json.parseToJsonElement(files.getValue(name))

        fun append(name: String, value: JsonObject) {
            val rows = element(name).jsonArray.toMutableList()
            rows += value
            files[name] = Json.encodeToString(JsonArray.serializer(), JsonArray(rows))
        }
    }
}
