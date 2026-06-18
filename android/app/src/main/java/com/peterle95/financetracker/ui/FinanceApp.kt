package com.peterle95.financetracker.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.automirrored.outlined.List
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AccountBalance
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.Dashboard
import androidx.compose.material.icons.outlined.PieChart
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.peterle95.financetracker.ui.screens.AddTransactionScreen
import com.peterle95.financetracker.ui.screens.BudgetScreen
import com.peterle95.financetracker.ui.screens.DashboardScreen
import com.peterle95.financetracker.ui.screens.NetWorthScreen
import com.peterle95.financetracker.ui.screens.SettingsScreen
import com.peterle95.financetracker.ui.screens.TransactionsScreen
import kotlinx.coroutines.flow.collectLatest

private data class Destination(
    val route: String,
    val label: String,
    val icon: @Composable () -> Unit,
)

private val destinations = listOf(
    Destination("dashboard", "Dashboard", { Icon(Icons.Outlined.Dashboard, contentDescription = null) }),
    Destination("add", "Add", { Icon(Icons.Outlined.Add, contentDescription = null) }),
    Destination("transactions", "Transactions", { Icon(Icons.AutoMirrored.Outlined.List, contentDescription = null) }),
    Destination("budget", "Budget", { Icon(Icons.Outlined.PieChart, contentDescription = null) }),
    Destination("net_worth", "Net Worth", { Icon(Icons.Outlined.AccountBalance, contentDescription = null) }),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FinanceApp(viewModel: FinanceViewModel) {
    val navController = rememberNavController()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(viewModel) {
        viewModel.messages.collectLatest { snackbarHostState.showSnackbar(it) }
    }

    val lifecycleOwner = LocalLifecycleOwner.current
    DisposableEffect(lifecycleOwner, viewModel) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                viewModel.reloadFromSyncedFile(showMessage = false)
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Finance Tracker") },
                actions = {
                    IconButton(onClick = { navController.navigate("settings") }) {
                        Icon(Icons.Outlined.Settings, contentDescription = "Settings")
                    }
                },
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
        bottomBar = {
            NavigationBar {
                val currentRoute = navController.currentBackStackEntryAsState().value?.destination?.route
                destinations.forEach { destination ->
                    NavigationBarItem(
                        selected = currentRoute == destination.route,
                        onClick = {
                            navController.navigate(destination.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = destination.icon,
                        label = { Text(destination.label) },
                    )
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = "dashboard",
            modifier = Modifier.padding(padding),
        ) {
            composable("dashboard") {
                DashboardScreen(
                    viewModel = viewModel,
                    onOpenBudget = { navController.navigate("budget") },
                    onOpenNetWorth = { navController.navigate("net_worth") },
                    onOpenSettings = { navController.navigate("settings") },
                )
            }
            composable("add") { AddTransactionScreen(viewModel) }
            composable("transactions") { TransactionsScreen(viewModel) }
            composable("budget") { BudgetScreen(viewModel) }
            composable("net_worth") { NetWorthScreen(viewModel) }
            composable("settings") { SettingsScreen(viewModel) }
        }
    }
}
