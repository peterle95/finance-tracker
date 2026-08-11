package com.peterle95.financetracker.data

import com.peterle95.financetracker.domain.BudgetSettings
import com.peterle95.financetracker.domain.CategoryDefaults
import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import java.text.Normalizer
import java.util.UUID

interface FinanceDirectory {
    suspend fun listFiles(): List<String>
    suspend fun readText(name: String): String?
    suspend fun writeText(name: String, content: String)
    suspend fun delete(name: String)
}

data class DirectoryLoadResult(
    val document: FinanceDocument,
    val warnings: List<String>,
    val migratedLegacy: Boolean = false,
)

class FinanceDirectoryStore(private val directory: FinanceDirectory) {
    private val json = Json { prettyPrint = true }
    private val _document = MutableStateFlow(FinanceDocument.empty())
    val document: StateFlow<FinanceDocument> = _document.asStateFlow()

    suspend fun reload(): DirectoryLoadResult {
        val migrated = ensureInitialized()
        val loaded = loadSplit()
        _document.value = loaded
        return DirectoryLoadResult(loaded, warnings(), migrated)
    }

    suspend fun addTransaction(
        type: TransactionType,
        date: String,
        amount: Double,
        category: String,
        description: String,
        behaviorDate: String?,
    ) {
        val target = categoryRecord(type, category)
        val filename = transactionFilename(type, target.fileKey)
        val rows = readArray(filename).toMutableList()
        rows += buildJsonObject {
            put("id", UUID.randomUUID().toString())
            put("date", date)
            put("amount", amount)
            put("category", target.name)
            put("description", description)
            behaviorDate?.takeIf { it.isNotBlank() }?.let { put("behavior_date", it) }
        }
        writeVerified(filename, JsonArray(rows))
        publishLatest()
    }

    suspend fun deleteTransaction(exportId: String) {
        require(exportId.isNotBlank()) { "This transaction has no JSON id and cannot be deleted from Android." }
        val location = findTransaction(exportId)
        val updated = readArray(location.filename).filterNot { it.idOrNull() == exportId }
        writeVerified(location.filename, JsonArray(updated))
        publishLatest()
    }

    suspend fun updateTransaction(
        exportId: String,
        type: TransactionType,
        date: String,
        amount: Double,
        category: String,
        description: String,
        behaviorDate: String?,
    ) {
        require(exportId.isNotBlank()) { "This transaction has no JSON id and cannot be modified from Android." }
        val source = findTransaction(exportId)
        val targetCategory = categoryRecord(type, category)
        val targetFilename = transactionFilename(type, targetCategory.fileKey)
        val old = source.rows.first { it.idOrNull() == exportId }.jsonObject
        val replacement = buildJsonObject {
            old.forEach { (key, value) ->
                if (key !in transactionKeys) put(key, value)
            }
            put("id", exportId)
            put("date", date)
            put("amount", amount)
            put("category", targetCategory.name)
            put("description", description)
            behaviorDate?.takeIf { it.isNotBlank() }?.let { put("behavior_date", it) }
        }
        if (targetFilename == source.filename) {
            val latest = readArray(source.filename)
            writeVerified(
                source.filename,
                JsonArray(latest.map { if (it.idOrNull() == exportId) replacement else it }),
            )
        } else {
            val destination = readArray(targetFilename).filterNot { it.idOrNull() == exportId } + replacement
            writeVerified(targetFilename, JsonArray(destination))
            writeVerified(source.filename, JsonArray(readArray(source.filename).filterNot { it.idOrNull() == exportId }))
        }
        publishLatest()
    }

    suspend fun setCategories(type: TransactionType, names: List<String>) {
        val normalized = names.map(String::trim).filter(String::isNotEmpty)
        require(normalized.distinctBy(String::lowercase).size == normalized.size) {
            "${type.label} category names must be non-empty and unique."
        }
        val root = readObject(CATEGORIES_FILE)
        val old = categoryRecords(root, type)
        val unused = old.toMutableList()
        val records = arrayOfNulls<CategoryRecord>(normalized.size)
        normalized.forEachIndexed { index, name ->
            unused.firstOrNull { it.name.equals(name, true) }?.let {
                records[index] = it.copy(name = name)
                unused.remove(it)
            }
        }
        val newIndexes = records.indices.filter { records[it] == null }.toMutableList()
        val positionalChanges = if (old.size == normalized.size) {
            old.indices.filter { !old[it].name.equals(normalized[it], true) }
        } else {
            emptyList()
        }
        if (positionalChanges.size == 1) {
            val index = positionalChanges.single()
            unused.firstOrNull { it == old[index] }?.let {
                records[index] = it.copy(name = normalized[index])
                unused.remove(it)
                newIndexes.remove(index)
            }
        }
        for (removed in unused) {
            val filename = transactionFilename(type, removed.fileKey)
            require(readArray(filename).isEmpty()) { "Cannot delete category with transactions: ${removed.name}" }
        }
        newIndexes.forEach { index ->
            val key = newFileKey(normalized[index], old + records.filterNotNull())
            records[index] = CategoryRecord(normalized[index], key)
            writeVerified(transactionFilename(type, key), JsonArray(emptyList()))
        }
        val renamedCategories = mutableListOf<Pair<String, String>>()
        records.filterNotNull().forEach { record ->
            val previous = old.firstOrNull { it.fileKey == record.fileKey } ?: return@forEach
            if (previous.name != record.name) {
                val filename = transactionFilename(type, record.fileKey)
                val renamed = readArray(filename).map { element ->
                    val row = element.jsonObject
                    if (row["category"]?.jsonPrimitive?.contentOrNull.equals(previous.name, true)) {
                        JsonObject(row + ("category" to JsonPrimitive(record.name)))
                    } else {
                        row
                    }
                }
                writeVerified(filename, JsonArray(renamed))
                renamedCategories += previous.name to record.name
            }
        }
        val updatedRoot = buildJsonObject {
            root.forEach { (key, value) -> if (key != type.label) put(key, value) }
            put(type.label, JsonArray(records.filterNotNull().map(CategoryRecord::toJson)))
        }
        writeVerified(CATEGORIES_FILE, updatedRoot)
        if (renamedCategories.isNotEmpty()) {
            val budget = readObject(BUDGET_FILE)
            val categoryBudgets = (budget["category_budgets"] as? JsonObject)?.toMutableMap() ?: mutableMapOf()
            val typeBudgets = (categoryBudgets[type.label] as? JsonObject)?.toMutableMap() ?: mutableMapOf()
            renamedCategories.forEach { (oldName, newName) ->
                typeBudgets.keys.firstOrNull { it.equals(oldName, true) }?.let { oldKey ->
                    typeBudgets[newName] = typeBudgets.remove(oldKey)!!
                }
            }
            categoryBudgets[type.label] = JsonObject(typeBudgets)
            writeVerified(BUDGET_FILE, JsonObject(budget + ("category_budgets" to JsonObject(categoryBudgets))))
        }
        unused.forEach { directory.delete(transactionFilename(type, it.fileKey)) }
        publishLatest()
    }

    suspend fun mutateOwner(owner: FileOwner, transform: (FinanceDocument) -> FinanceDocument) {
        val latest = loadSplit()
        val updated = transform(latest)
        val normalizedLatest = latest.budgetSettingsModel.toJsonObjectPreserving(latest.budgetSettings)
        when (owner) {
            FileOwner.Budget -> writeSettingsOwner(
                BUDGET_FILE,
                budgetKeys.filterTo(mutableSetOf()) { normalizedLatest[it] != updated.budgetSettings[it] },
                updated.budgetSettings,
            )
            FileOwner.NetWorth -> writeSettingsOwner(
                NET_WORTH_FILE,
                netWorthKeys.filterTo(mutableSetOf()) { normalizedLatest[it] != updated.budgetSettings[it] },
                updated.budgetSettings,
            )
            FileOwner.Loans -> {
                writeVerified(LOANS_FILE, updated.budgetSettings["loans"] as? JsonArray ?: JsonArray(emptyList()))
                val raw = readObject(NET_WORTH_FILE)
                val currentBalance = raw["money_lent_balance"]?.jsonPrimitive?.doubleOrNull ?: 0.0
                val delta = updated.budgetSettingsModel.balances.moneyLent - latest.budgetSettingsModel.balances.moneyLent
                writeVerified(
                    NET_WORTH_FILE,
                    JsonObject(raw + ("money_lent_balance" to JsonPrimitive(currentBalance + delta))),
                )
            }
            FileOwner.SavingsGoals -> writeVerified(
                SAVINGS_GOALS_FILE,
                updated.budgetSettings["savings_goals"] as? JsonArray ?: JsonArray(emptyList()),
            )
        }
        publishLatest()
    }

    private suspend fun ensureInitialized(): Boolean {
        if (directory.readText(CATEGORIES_FILE) != null) return false
        val legacyText = directory.readText(LEGACY_FILE)
        if (legacyText != null) {
            migrateLegacy(legacyText)
            return true
        }
        require(directory.listFiles().isEmpty()) {
            "$CATEGORIES_FILE is missing; refusing to initialize a non-empty directory."
        }
        createDefaults()
        return false
    }

    private suspend fun createDefaults() {
        val categories = defaultCategoryRoot()
        defaultStaticFiles().forEach { (name, value) -> writeVerified(name, value) }
        for (type in TransactionType.entries) {
            categoryRecords(categories, type).forEach {
                writeVerified(transactionFilename(type, it.fileKey), JsonArray(emptyList()))
            }
        }
        writeVerified(CATEGORIES_FILE, categories)
    }

    private suspend fun migrateLegacy(content: String) {
        val root = json.parseToJsonElement(content) as? JsonObject ?: error("Legacy finance_data.json must be an object.")
        require(root["expenses"] == null || root["expenses"] is JsonArray) { "Legacy expenses must be an array." }
        require(root["incomes"] == null || root["incomes"] is JsonArray) { "Legacy incomes must be an array." }
        require(root["budget_settings"] == null || root["budget_settings"] is JsonObject) {
            "Legacy budget_settings must be an object."
        }
        require(root["categories"] == null || root["categories"] is JsonObject) { "Legacy categories must be an object." }

        val assignedRoot = JsonObject(root.mapValues { (key, value) ->
            if (key !in setOf("expenses", "incomes") || value !is JsonArray) {
                value
            } else {
                JsonArray(value.map { element ->
                    require(element is JsonObject) { "Legacy transactions must be objects." }
                    if (element.idOrNull() == null) {
                        JsonObject(element + ("id" to JsonPrimitive(UUID.randomUUID().toString())))
                    } else {
                        element
                    }
                })
            }
        })
        val categories = migrationCategories(assignedRoot)
        val budget = root["budget_settings"] as? JsonObject ?: JsonObject(emptyMap())
        val desired = splitSettings(budget, root)
        val normalizedArrays = mutableMapOf<String, JsonArray>()
        for (type in TransactionType.entries) {
            val rootKey = if (type == TransactionType.Expense) "expenses" else "incomes"
            val source = assignedRoot[rootKey] as? JsonArray
                ?: JsonArray(emptyList())
            val records = categoryRecords(categories, type)
            val normalized = source.map { element ->
                val row = element.jsonObject
                val category = row["category"]?.jsonPrimitive?.contentOrNull.orEmpty()
                val canonical = records.firstOrNull { it.name.equals(category, true) }?.name ?: category
                JsonObject(row + ("category" to JsonPrimitive(canonical)))
            }
            normalizedArrays[rootKey] = JsonArray(normalized)
            val grouped = normalized.groupBy { it["category"]?.jsonPrimitive?.contentOrNull.orEmpty() }
            records.forEach { record ->
                val rows = grouped.entries.firstOrNull { it.key.equals(record.name, true) }?.value.orEmpty()
                desired[transactionFilename(type, record.fileKey)] = JsonArray(rows)
            }
        }
        desired.forEach { (name, value) -> writeVerified(name, value) }
        writeVerified(CATEGORIES_FILE, categories)
        val expected = FinanceJsonCodec.parse(encode(buildJsonObject {
            assignedRoot.forEach { (key, value) ->
                when (key) {
                    "expenses", "incomes", "categories", "budget_settings" -> Unit
                    else -> put(key, value)
                }
            }
            put("expenses", normalizedArrays.getValue("expenses"))
            put("incomes", normalizedArrays.getValue("incomes"))
            put("budget_settings", buildJsonObject {
                budget.forEach(::put)
                if ("loans" !in budget) put("loans", JsonArray(emptyList()))
                if ("savings_goals" !in budget) put("savings_goals", JsonArray(emptyList()))
            })
            put("categories", buildJsonObject {
                TransactionType.entries.forEach { type ->
                    put(type.label, JsonArray(categoryRecords(categories, type).map { JsonPrimitive(it.name) }))
                }
            })
        }))
        val reconstructed = loadSplit()
        if (semantic(reconstructed) != semantic(expected)) {
            directory.delete(CATEGORIES_FILE)
            error("Migration verification failed; finance_data.json was left untouched.")
        }
    }

    private suspend fun loadSplit(): FinanceDocument {
        val categoriesRoot = readObject(CATEGORIES_FILE)
        val budget = settingsFromOwner(readObject(BUDGET_FILE), budgetKeys)
        val netWorth = settingsFromOwner(readObject(NET_WORTH_FILE), netWorthKeys)
        val preferences = readObject(PREFERENCES_FILE)
        val preferenceExtra = preferences["_extra"] as? JsonObject ?: JsonObject(emptyMap())
        val settings = buildJsonObject {
            budget.forEach(::put)
            netWorth.forEach(::put)
            preferences.forEach { (key, value) -> if (key in preferenceKeys) put(key, value) }
            (preferenceExtra["legacy_budget_settings"] as? JsonObject)?.forEach(::put)
            put("loans", readArray(LOANS_FILE))
            put("savings_goals", readArray(SAVINGS_GOALS_FILE))
        }
        val expenses = mutableListOf<JsonElement>()
        val incomes = mutableListOf<JsonElement>()
        for (type in TransactionType.entries) {
            val target = if (type == TransactionType.Expense) expenses else incomes
            categoryRecords(categoriesRoot, type).forEach { record ->
                val filename = transactionFilename(type, record.fileKey)
                if (directory.readText(filename) == null) writeVerified(filename, JsonArray(emptyList()))
                var changed = false
                val rows = readArray(filename).map { element ->
                    val row = element as? JsonObject ?: error("$filename must contain transaction objects.")
                    val withId = if (row.idOrNull() == null) {
                        changed = true
                        JsonObject(row + ("id" to JsonPrimitive(UUID.randomUUID().toString())))
                    } else {
                        row
                    }
                    JsonObject(withId + ("category" to JsonPrimitive(record.name)))
                }
                if (changed) writeVerified(filename, JsonArray(rows))
                target += rows
            }
        }
        val rootExtra = preferenceExtra["legacy_root"] as? JsonObject ?: JsonObject(emptyMap())
        return FinanceJsonCodec.parse(
            encode(buildJsonObject {
                rootExtra.forEach(::put)
                put("expenses", JsonArray(expenses))
                put("incomes", JsonArray(incomes))
                put("budget_settings", settings)
                put("categories", buildJsonObject {
                    put("Expense", JsonArray(categoryRecords(categoriesRoot, TransactionType.Expense).map { JsonPrimitive(it.name) }))
                    put("Income", JsonArray(categoryRecords(categoriesRoot, TransactionType.Income).map { JsonPrimitive(it.name) }))
                })
            }),
        )
    }

    private suspend fun publishLatest() {
        _document.value = loadSplit()
    }

    private suspend fun findTransaction(id: String): TransactionLocation {
        val categories = readObject(CATEGORIES_FILE)
        for (type in TransactionType.entries) {
            for (record in categoryRecords(categories, type)) {
                val filename = transactionFilename(type, record.fileKey)
                val rows = readArray(filename)
                if (rows.any { it.idOrNull() == id }) return TransactionLocation(filename, rows)
            }
        }
        error("Transaction not found.")
    }

    private suspend fun categoryRecord(type: TransactionType, name: String): CategoryRecord =
        categoryRecords(readObject(CATEGORIES_FILE), type).firstOrNull { it.name.equals(name, true) }
            ?: error("Unknown ${type.label} category: $name")

    private suspend fun writeSettingsOwner(filename: String, keys: Set<String>, settings: JsonObject) {
        if (keys.isEmpty()) return
        val raw = readObject(filename)
        writeVerified(filename, buildJsonObject {
            raw.forEach(::put)
            keys.forEach { key -> settings[key]?.let { put(key, it) } }
        })
    }

    private fun settingsFromOwner(raw: JsonObject, keys: Set<String>) = buildJsonObject {
        raw.forEach { (key, value) -> if (key in keys) put(key, value) }
        (raw["_extra"] as? JsonObject)?.forEach(::put)
        raw.forEach { (key, value) -> if (key !in keys && key != "_extra") put(key, value) }
    }

    suspend fun warnings(): List<String> {
        val expected = buildSet {
            val categories = readObject(CATEGORIES_FILE)
            TransactionType.entries.forEach { type ->
                categoryRecords(categories, type).forEach { add(transactionFilename(type, it.fileKey)) }
            }
        }
        return directory.listFiles().mapNotNull { name ->
            when {
                "conflict" in name.lowercase() -> "Sync conflict file detected: $name"
                name.startsWith("transactions_") && name.endsWith(".json") && name !in expected ->
                    "Orphan transaction file detected: $name"
                else -> null
            }
        }.sorted()
    }

    private suspend fun readObject(name: String): JsonObject =
        directory.readText(name)?.let { json.parseToJsonElement(it) as? JsonObject }
            ?: error("$name is missing or is not a JSON object.")

    private suspend fun readArray(name: String): JsonArray =
        directory.readText(name)?.let { json.parseToJsonElement(it) as? JsonArray }
            ?: error("$name is missing or is not a JSON array.")

    private suspend fun writeVerified(name: String, value: JsonElement) {
        val content = encode(value)
        directory.writeText(name, content)
        val written = directory.readText(name) ?: error("Could not verify $name after writing.")
        require(json.parseToJsonElement(written) == value) { "$name did not verify after writing." }
    }

    private fun migrationCategories(root: JsonObject): JsonObject {
        val raw = root["categories"] as? JsonObject
        return buildJsonObject {
            TransactionType.entries.forEach { type ->
                val defaults = if (type == TransactionType.Expense) CategoryDefaults.expense else CategoryDefaults.income
                val names = (raw?.get(type.label) as? JsonArray)?.mapNotNull {
                    it.jsonPrimitive.contentOrNull?.trim()?.takeIf(String::isNotEmpty)
                }?.toMutableList() ?: defaults.toMutableList()
                val source = root[if (type == TransactionType.Expense) "expenses" else "incomes"] as? JsonArray
                source.orEmpty().forEach { element ->
                    val name = (element as? JsonObject)?.get("category")?.jsonPrimitive?.contentOrNull?.trim().orEmpty()
                    if (name.isNotEmpty() && names.none { it.equals(name, true) }) names += name
                }
                val records = mutableListOf<CategoryRecord>()
                names.forEach { name -> records += CategoryRecord(name, newFileKey(name, records)) }
                put(type.label, JsonArray(records.map(CategoryRecord::toJson)))
            }
        }
    }

    private fun splitSettings(settings: JsonObject, root: JsonObject): MutableMap<String, JsonElement> {
        val unknown = JsonObject(settings.filterKeys {
            it !in budgetKeys && it !in netWorthKeys && it !in preferenceKeys && it !in setOf("loans", "savings_goals")
        })
        return mutableMapOf(
            BUDGET_FILE to ownerObject(settings, budgetKeys),
            NET_WORTH_FILE to ownerObject(settings, netWorthKeys),
            LOANS_FILE to (settings["loans"] as? JsonArray ?: JsonArray(emptyList())),
            SAVINGS_GOALS_FILE to (settings["savings_goals"] as? JsonArray ?: JsonArray(emptyList())),
            PREFERENCES_FILE to buildJsonObject {
                preferenceKeys.forEach { key -> settings[key]?.let { put(key, it) } }
                put("_extra", buildJsonObject {
                    if (unknown.isNotEmpty()) put("legacy_budget_settings", unknown)
                    val rootExtra = JsonObject(root.filterKeys { it !in legacyRootKeys })
                    if (rootExtra.isNotEmpty()) put("legacy_root", rootExtra)
                })
            },
        )
    }

    private fun ownerObject(settings: JsonObject, keys: Set<String>) = buildJsonObject {
        keys.forEach { key -> settings[key]?.let { put(key, it) } }
        put("_extra", JsonObject(emptyMap()))
    }

    private fun defaultStaticFiles(): Map<String, JsonElement> = mapOf(
        BUDGET_FILE to buildJsonObject {
            put("monthly_income", JsonArray(emptyList()))
            put("fixed_costs", JsonArray(emptyList()))
            put("daily_savings_goal", 0)
            put("category_budgets", buildJsonObject {
                put("Expense", JsonObject(emptyMap()))
                put("Income", JsonObject(emptyMap()))
            })
            put("_extra", JsonObject(emptyMap()))
        },
        NET_WORTH_FILE to buildJsonObject {
            (netWorthKeys - "asset_snapshots").forEach { put(it, 0) }
            put("asset_snapshots", JsonArray(emptyList()))
            put("_extra", JsonObject(emptyMap()))
        },
        LOANS_FILE to JsonArray(emptyList()),
        SAVINGS_GOALS_FILE to JsonArray(emptyList()),
        PREFERENCES_FILE to buildJsonObject {
            put("ai_settings", buildJsonObject { put("api_key", "") })
            put("default_behaviors", JsonObject(emptyMap()))
            put("default_ranges", JsonObject(emptyMap()))
            put("_extra", JsonObject(emptyMap()))
        },
    )

    private fun defaultCategoryRoot() = buildJsonObject {
        put("Expense", JsonArray(defaultRecords(CategoryDefaults.expense).map(CategoryRecord::toJson)))
        put("Income", JsonArray(defaultRecords(CategoryDefaults.income).map(CategoryRecord::toJson)))
    }

    private fun defaultRecords(names: List<String>): List<CategoryRecord> {
        val records = mutableListOf<CategoryRecord>()
        names.forEach { records += CategoryRecord(it, newFileKey(it, records)) }
        return records
    }

    private fun categoryRecords(root: JsonObject, type: TransactionType): List<CategoryRecord> =
        (root[type.label] as? JsonArray)?.map { element ->
            val value = element as? JsonObject ?: error("${type.label} categories must be objects.")
            val name = value["name"]?.jsonPrimitive?.contentOrNull?.trim().orEmpty()
            val key = value["file_key"]?.jsonPrimitive?.contentOrNull?.trim().orEmpty()
            require(name.isNotEmpty() && key.matches(fileKeyRegex)) { "Invalid ${type.label} category entry." }
            CategoryRecord(name, key, JsonObject(value.filterKeys { it !in setOf("name", "file_key") }))
        }?.also { records ->
            require(records.distinctBy { it.name.lowercase() }.size == records.size) {
                "Duplicate ${type.label} category name."
            }
            require(records.distinctBy { it.fileKey.lowercase() }.size == records.size) {
                "Duplicate ${type.label} category file_key."
            }
        } ?: error("categories.json is missing ${type.label} categories.")

    private fun newFileKey(name: String, records: List<CategoryRecord>): String {
        val base = Normalizer.normalize(name, Normalizer.Form.NFKD)
            .replace(Regex("\\p{M}+"), "")
            .lowercase()
            .replace(Regex("[^a-z0-9]+"), "-")
            .trim('-')
            .ifEmpty { "category" }
        val used = records.map { it.fileKey.lowercase() }.toSet()
        var key = base
        var suffix = 2
        while (key.lowercase() in used) key = "${base}-${suffix++}"
        return key
    }

    private fun semantic(document: FinanceDocument) = document.copy(
        records = document.records.sortedWith(
            compareBy<FinanceRecord> { it.transaction.type.ordinal }
                .thenBy { it.transaction.exportId },
        ),
    )

    private fun encode(value: JsonElement): String = json.encodeToString(JsonElement.serializer(), value)

    private data class CategoryRecord(val name: String, val fileKey: String, val extra: JsonObject = JsonObject(emptyMap())) {
        fun toJson() = buildJsonObject {
            extra.forEach { (key, value) -> if (key !in setOf("name", "file_key")) put(key, value) }
            put("name", name)
            put("file_key", fileKey)
        }
    }

    private data class TransactionLocation(val filename: String, val rows: List<JsonElement>)

    companion object {
        private const val LEGACY_FILE = "finance_data.json"
        private const val CATEGORIES_FILE = "categories.json"
        private const val BUDGET_FILE = "budget.json"
        private const val NET_WORTH_FILE = "net_worth.json"
        private const val LOANS_FILE = "loans.json"
        private const val SAVINGS_GOALS_FILE = "savings_goals.json"
        private const val PREFERENCES_FILE = "preferences.json"
        private val budgetKeys = setOf("monthly_income", "fixed_costs", "daily_savings_goal", "category_budgets")
        private val netWorthKeys = setOf(
            "bank_account_balance", "wallet_balance", "savings_balance", "investment_balance",
            "money_lent_balance", "cash_balance", "asset_snapshots",
        )
        private val preferenceKeys = setOf("ai_settings", "default_behaviors", "default_ranges")
        private val legacyRootKeys = setOf("expenses", "incomes", "budget_settings", "categories")
        private val transactionKeys = setOf("id", "date", "amount", "category", "description", "behavior_date")
        private val fileKeyRegex = Regex("[a-z0-9]+(?:-[a-z0-9]+)*")

        fun transactionFilename(type: TransactionType, fileKey: String) =
            "transactions_${type.label.lowercase()}_$fileKey.json"
    }
}

enum class FileOwner { Budget, NetWorth, Loans, SavingsGoals }

private fun JsonElement.idOrNull(): String? =
    (this as? JsonObject)?.get("id")?.jsonPrimitive?.contentOrNull
