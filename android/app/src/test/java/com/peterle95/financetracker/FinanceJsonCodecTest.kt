package com.peterle95.financetracker

import com.peterle95.financetracker.data.FinanceJsonCodec
import com.peterle95.financetracker.data.FinanceMetadataEntity
import com.peterle95.financetracker.domain.CategoryDefaults
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class FinanceJsonCodecTest {
    @Test
    fun importParsesDesktopJsonAndPreservesUnknownFields() {
        val parsed = FinanceJsonCodec.parse(
            """
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
                  "id": "123.45",
                  "date": "2026-06-01",
                  "amount": 1000,
                  "category": "Salary",
                  "description": "Pay"
                }
              ],
              "budget_settings": { "bank_account_balance": 42 },
              "unexpected_root": true
            }
            """.trimIndent(),
            nowMillis = 1L,
        )

        assertEquals(2, parsed.transactions.size)
        val expense = parsed.transactions.first { it.type == "Expense" }
        assertNull(expense.exportId)
        assertEquals("2026-06-09", expense.behaviorDate)
        assertTrue(expense.extraJson.contains("note"))
        assertEquals(CategoryDefaults.expense, parsed.categories.expenses)
        assertEquals(42.0, parsed.budgetSettings["bank_account_balance"]!!.jsonPrimitive.content.toDouble(), 0.0)
        assertTrue(parsed.topLevelExtra.containsKey("unexpected_root"))
    }

    @Test
    fun exportReconstructsCompatibleDesktopJson() {
        val parsed = FinanceJsonCodec.parse(
            """
            {
              "expenses": [
                { "date": "2026-06-10", "amount": 12.5, "category": "Food", "description": "Lunch", "note": "kept" }
              ],
              "incomes": [
                { "id": "123.45", "date": "2026-06-01", "amount": 1000, "category": "Salary", "description": "Pay" }
              ],
              "budget_settings": { "wallet_balance": 7 },
              "categories": { "Expense": ["Food"], "Income": ["Salary"] },
              "unexpected_root": "kept"
            }
            """.trimIndent(),
            nowMillis = 1L,
        )

        val exported = FinanceJsonCodec.encode(
            transactions = parsed.transactions,
            metadata = FinanceMetadataEntity(
                budgetSettingsJson = Json.encodeToString(kotlinx.serialization.json.JsonObject.serializer(), parsed.budgetSettings),
                topLevelExtraJson = Json.encodeToString(kotlinx.serialization.json.JsonObject.serializer(), parsed.topLevelExtra),
            ),
            categories = parsed.categories,
        )
        val root = Json.parseToJsonElement(exported).jsonObject

        assertEquals("kept", root["unexpected_root"]!!.jsonPrimitive.content)
        assertEquals(1, root["expenses"]!!.jsonArray.size)
        assertEquals(1, root["incomes"]!!.jsonArray.size)
        assertNull(root["expenses"]!!.jsonArray[0].jsonObject["id"])
        assertEquals("123.45", root["incomes"]!!.jsonArray[0].jsonObject["id"]!!.jsonPrimitive.content)
        assertEquals("kept", root["expenses"]!!.jsonArray[0].jsonObject["note"]!!.jsonPrimitive.content)
    }
}
