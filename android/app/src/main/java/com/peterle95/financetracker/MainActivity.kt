package com.peterle95.financetracker

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.viewmodel.compose.viewModel
import com.peterle95.financetracker.ui.FinanceApp
import com.peterle95.financetracker.ui.FinanceViewModel
import com.peterle95.financetracker.ui.theme.FinanceTrackerTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            FinanceTrackerTheme {
                val viewModel: FinanceViewModel = viewModel()
                FinanceApp(viewModel = viewModel)
            }
        }
    }
}
