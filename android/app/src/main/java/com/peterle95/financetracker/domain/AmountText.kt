package com.peterle95.financetracker.domain

import java.util.Locale

fun formatAmountField(value: Double): String =
    if (value == 0.0) "0" else String.format(Locale.US, "%.2f", value)

fun parseAmountText(value: String): Double? {
    val compact = value
        .trim()
        .replace("€", "")
        .replace(" ", "")
        .replace("\u00A0", "")
    if (compact.isBlank()) return 0.0

    val lastComma = compact.lastIndexOf(',')
    val lastDot = compact.lastIndexOf('.')
    val normalized = when {
        lastComma >= 0 && lastDot >= 0 -> {
            if (lastComma > lastDot) {
                compact.replace(".", "").replace(',', '.')
            } else {
                compact.replace(",", "")
            }
        }

        lastComma >= 0 -> {
            if (compact.hasThousandsGrouping(',')) {
                compact.replace(",", "")
            } else {
                compact.replace(',', '.')
            }
        }

        else -> compact
    }

    return normalized.toDoubleOrNull()
}

private fun String.hasThousandsGrouping(separator: Char): Boolean {
    val signless = removePrefix("-").removePrefix("+")
    val groups = signless.split(separator)
    return groups.size > 1 &&
        groups.first().length in 1..3 &&
        groups.drop(1).all { it.length == 3 && it.all(Char::isDigit) } &&
        groups.first().all(Char::isDigit)
}
