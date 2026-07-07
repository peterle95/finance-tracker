package com.peterle95.financetracker.domain

import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit
import kotlin.math.max

data class SavingsGoalProgress(
    val progressPercent: Double,
    val remaining: Double,
    val isComplete: Boolean,
)

data class SavingsGoalsSummary(
    val totalGoals: Int,
    val activeGoals: Int,
    val completedGoals: Int,
    val totalTarget: Double,
    val totalAllocated: Double,
    val overallProgress: Double,
    val totalSavings: Double,
    val unallocated: Double,
)

object SavingsGoals {
    fun progress(goal: SavingsGoal): SavingsGoalProgress {
        val progressPercent = if (goal.targetAmount > 0.0) {
            goal.allocatedAmount / goal.targetAmount * 100.0
        } else {
            0.0
        }
        return SavingsGoalProgress(
            progressPercent = progressPercent,
            remaining = max(goal.targetAmount - goal.allocatedAmount, 0.0),
            isComplete = goal.allocatedAmount >= goal.targetAmount,
        )
    }

    fun totalAllocated(settings: BudgetSettings): Double =
        settings.savingsGoals.sumOf { it.allocatedAmount }

    fun unallocatedSavings(settings: BudgetSettings): Double =
        max(settings.balances.savings - totalAllocated(settings), 0.0)

    fun availableForGoal(settings: BudgetSettings, goalKey: String): Double =
        settings.balances.savings -
            settings.savingsGoals
                .filterNot { it.key == goalKey }
                .sumOf { it.allocatedAmount }

    fun summary(settings: BudgetSettings): SavingsGoalsSummary {
        val totalTarget = settings.savingsGoals.sumOf { it.targetAmount }
        val totalAllocated = totalAllocated(settings)
        val completed = settings.savingsGoals.count { progress(it).isComplete }
        return SavingsGoalsSummary(
            totalGoals = settings.savingsGoals.size,
            activeGoals = settings.savingsGoals.size - completed,
            completedGoals = completed,
            totalTarget = totalTarget,
            totalAllocated = totalAllocated,
            overallProgress = if (totalTarget > 0.0) totalAllocated / totalTarget * 100.0 else 0.0,
            totalSavings = settings.balances.savings,
            unallocated = max(settings.balances.savings - totalAllocated, 0.0),
        )
    }

    fun sortedGoals(goals: List<SavingsGoal>): List<SavingsGoal> {
        val active = goals.filterNot { progress(it).isComplete }
            .sortedWith(
                compareBy<SavingsGoal> { priorityOrder(it.priority) }
                    .thenBy { it.name.lowercase() },
            )
        val completed = goals.filter { progress(it).isComplete }
            .sortedBy { it.name.lowercase() }
        return active + completed
    }

    fun autoDistribute(settings: BudgetSettings): BudgetSettings {
        val totalSavings = settings.balances.savings
        require(settings.savingsGoals.isNotEmpty()) { "No goals to distribute savings to." }
        require(totalSavings > 0.0) { "No savings available to distribute." }

        var remainingSavings = totalSavings
        val activeGoals = settings.savingsGoals
            .map { it.copy(allocatedAmount = 0.0, completionDate = null) }
            .sortedWith(
                compareByDescending<SavingsGoal> { priorityRank(it.priority) }
                    .thenByDescending {
                        if (it.targetAmount > 0.0) it.allocatedAmount / it.targetAmount else 0.0
                    },
            )
        val distributedByKey = activeGoals.associate { goal ->
            if (remainingSavings <= 0.0) {
                goal.key to goal
            } else {
                val allocation = minOf(goal.targetAmount, remainingSavings)
                remainingSavings -= allocation
                goal.key to goal.copy(
                    allocatedAmount = allocation,
                    completionDate = if (allocation >= goal.targetAmount) todayIsoDate() else null,
                )
            }
        }
        return settings.copy(savingsGoals = settings.savingsGoals.map { distributedByKey[it.key] ?: it })
    }

    fun reportText(settings: BudgetSettings, today: LocalDate = LocalDate.now()): String {
        val goals = settings.savingsGoals
        val summary = summary(settings)
        val active = goals.filterNot { progress(it).isComplete }
        val completed = goals.filter { progress(it).isComplete }

        return buildString {
            appendLine("================================================================================")
            appendLine("SAVINGS GOALS REPORT")
            appendLine("================================================================================")
            appendLine()
            appendLine("Generated: ${today.format(DateTimeFormatter.ofPattern("MMMM d, yyyy"))}")
            appendLine("Note: The completion estimate is based on the average monthly allocation to the goal since its creation.")
            appendLine()
            appendLine("--------------------------------------------------------------------------------")
            appendLine()
            appendLine("SAVINGS SUMMARY")
            appendLine("--------------------------------------------------------------------------------")
            appendLine("Total Savings Balance:        ${eur(summary.totalSavings)}")
            appendLine("Amount Allocated to Goals:    ${eur(summary.totalAllocated)}")
            appendLine("Unallocated Savings:          ${eur(summary.unallocated)}")
            appendLine()
            appendLine("Total Goals:                  ${summary.totalGoals}")
            appendLine("Active Goals:                 ${summary.activeGoals}")
            appendLine("Completed Goals:              ${summary.completedGoals}")
            appendLine("Total Target Amount:          ${eur(summary.totalTarget)}")
            appendLine("Overall Progress:             ${"%.1f".format(summary.overallProgress)}%")
            appendLine()

            if (goals.isEmpty()) {
                appendLine("No savings goals set. Create your first goal to start tracking.")
                return@buildString
            }

            if (summary.unallocated > 0.0) {
                appendLine("You have ${eur(summary.unallocated)} in unallocated savings.")
                appendLine("Consider allocating this to your goals.")
                appendLine()
            }

            if (active.isNotEmpty()) {
                appendLine("================================================================================")
                appendLine("ACTIVE GOALS")
                appendLine("================================================================================")
                appendLine()
                active.forEach { goal ->
                    val progress = progress(goal)
                    appendLine("Goal: ${goal.name}")
                    if (goal.description.isNotBlank()) appendLine("Description: ${goal.description}")
                    appendLine("----------------------------------------")
                    appendLine("Target Amount:         ${eur(goal.targetAmount)}")
                    appendLine("Allocated Savings:     ${eur(goal.allocatedAmount)}")
                    appendLine("Still Needed:          ${eur(progress.remaining)}")
                    appendLine("Progress:              ${"%.1f".format(progress.progressPercent)}%")
                    goal.targetDate?.let {
                        appendLine("Target Date:           $it")
                        appendLine("Required Monthly:      ${requiredMonthly(goal, today)}")
                    }
                    appendLine("Completion Estimate:   ${completionEstimate(goal, today)}")
                    appendLine("[${bar(progress.progressPercent)}] ${"%.1f".format(progress.progressPercent)}%")
                    appendLine()
                }
            }

            if (completed.isNotEmpty()) {
                appendLine("================================================================================")
                appendLine("COMPLETED GOALS")
                appendLine("================================================================================")
                appendLine()
                completed.forEach { goal ->
                    appendLine("${goal.name} - ${eur(goal.targetAmount)}")
                    goal.completionDate?.let { appendLine("  Completed: $it") }
                    appendLine()
                }
            }
        }
    }

    private fun priorityOrder(priority: String): Int =
        when (priority) {
            "High" -> 0
            "Medium" -> 1
            "Low" -> 2
            else -> 1
        }

    private fun priorityRank(priority: String): Int =
        when (priority) {
            "High" -> 3
            "Medium" -> 2
            "Low" -> 1
            else -> 2
        }

    private fun completionEstimate(goal: SavingsGoal, today: LocalDate): String {
        val remaining = goal.targetAmount - goal.allocatedAmount
        if (remaining <= 0.0) return "Goal already achieved."
        if (goal.allocatedAmount <= 0.0) return "Allocate funds to estimate completion."

        val createdDate = runCatching { LocalDate.parse(goal.createdDate) }.getOrNull()
            ?: return "Cannot estimate without a creation date."
        val daysSinceCreation = max(ChronoUnit.DAYS.between(createdDate, today).toDouble(), 30.0)
        val averageMonthlySavings = goal.allocatedAmount / (daysSinceCreation / 30.0)
        if (averageMonthlySavings <= 0.0) return "No average monthly savings to estimate completion."

        val daysNeeded = (remaining / averageMonthlySavings * 30.0).toLong()
        val completionDate = today.plusDays(daysNeeded)
        return "Estimated: ${completionDate.format(DateTimeFormatter.ofPattern("MMMM yyyy"))}"
    }

    private fun requiredMonthly(goal: SavingsGoal, today: LocalDate): String {
        val targetDate = goal.targetDate?.let { runCatching { LocalDate.parse(it) }.getOrNull() }
            ?: return "No target date set."
        val remaining = goal.targetAmount - goal.allocatedAmount
        if (remaining <= 0.0) return "Goal already achieved."
        if (!targetDate.isAfter(today)) return "OVERDUE - Remaining: ${eur(remaining)}"

        val monthsRemaining = max(ChronoUnit.DAYS.between(today, targetDate).toDouble() / 30.0, 1.0)
        return "${eur(remaining / monthsRemaining)}/month"
    }

    private fun bar(progressPercent: Double): String {
        val filled = (progressPercent.coerceIn(0.0, 100.0) / 100.0 * 40).toInt()
        return "#".repeat(filled) + "-".repeat(40 - filled)
    }

    private fun eur(value: Double): String =
        "EUR %,.2f".format(value)
}
