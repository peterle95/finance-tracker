package com.peterle95.financetracker

import com.peterle95.financetracker.domain.formatAmountField
import com.peterle95.financetracker.domain.parseAmountText
import org.junit.Assert.assertEquals
import org.junit.Test
import java.util.Locale

class AmountTextTest {
    @Test
    fun fieldFormattingUsesDotDecimalRegardlessOfDefaultLocale() {
        val previous = Locale.getDefault()
        try {
            Locale.setDefault(Locale.GERMANY)

            assertEquals("1.23", formatAmountField(1.23))
        } finally {
            Locale.setDefault(previous)
        }
    }

    @Test
    fun parserAcceptsDotAndCommaDecimals() {
        assertEquals(1.23, parseAmountText("1.23")!!, 0.0)
        assertEquals(1.23, parseAmountText("1,23")!!, 0.0)
    }

    @Test
    fun parserDistinguishesCommonThousandsSeparators() {
        assertEquals(1234.56, parseAmountText("1,234.56")!!, 0.0)
        assertEquals(1234.56, parseAmountText("1.234,56")!!, 0.0)
        assertEquals(1234.0, parseAmountText("1,234")!!, 0.0)
    }
}
