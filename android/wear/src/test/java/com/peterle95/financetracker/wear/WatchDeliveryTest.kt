package com.peterle95.financetracker.wear

import org.junit.Assert.assertEquals
import org.junit.Test

class WatchDeliveryTest {
    @Test
    fun noPendingSubmissionSucceeds() {
        assertEquals(DeliveryResult.Success, deliveryResult(DeliveryAttempt.NotNeeded, hasPending = false))
    }

    @Test
    fun unreachablePhoneOrSendFailureRetries() {
        assertEquals(DeliveryResult.Retry, deliveryResult(DeliveryAttempt.Failed, hasPending = false))
    }

    @Test
    fun successfulSendWithoutAcknowledgementRetries() {
        assertEquals(DeliveryResult.Retry, deliveryResult(DeliveryAttempt.Succeeded, hasPending = true))
    }

    @Test
    fun terminalAcknowledgementSucceeds() {
        assertEquals(DeliveryResult.Success, deliveryResult(DeliveryAttempt.Succeeded, hasPending = false))
    }
}
