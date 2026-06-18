package com.dailyread.app.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.dailyread.app.ui.screens.articles.AddArticleScreen
import com.dailyread.app.ui.screens.articles.ArticlesScreen
import com.dailyread.app.ui.screens.home.HomeScreen
import com.dailyread.app.ui.screens.random.RandomReadScreen
import com.dailyread.app.ui.screens.reader.ReaderScreen
import com.dailyread.app.ui.screens.acupoint.AcupointScreen
import com.dailyread.app.ui.screens.acupoint.AcupointManageScreen
import com.dailyread.app.ui.screens.acupoint.AddAcupointScreen
import com.dailyread.app.ui.screens.concept.ConceptScreen
import com.dailyread.app.ui.screens.concept.ConceptManageScreen
import com.dailyread.app.ui.screens.concept.AddConceptScreen
import com.dailyread.app.ui.screens.settings.SettingsScreen
import com.dailyread.app.ui.screens.stats.StatsScreen
import com.dailyread.app.ui.utils.AdaptiveLayoutConfig

@Composable
fun AppNavigation(
    navController: NavHostController,
    layoutConfig: AdaptiveLayoutConfig,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = Screen.Home.route,
        modifier = modifier
    ) {
        composable(Screen.Home.route) {
            HomeScreen(
                onNavigateToArticle = { articleId ->
                    navController.navigate("${Screen.Reader.route}/$articleId")
                },
                onNavigateToAddArticle = {
                    navController.navigate(Screen.AddArticle.route)
                },
                onNavigateToBottomNav = { route ->
                    navigateToRoute(navController, route)
                },
                layoutConfig = layoutConfig
            )
        }

        composable(
            "${Screen.Reader.route}/{articleId}",
            arguments = listOf(navArgument("articleId") { type = NavType.LongType })
        ) { backStackEntry ->
            val articleId = backStackEntry.arguments?.getLong("articleId") ?: 0L
            ReaderScreen(
                articleId = articleId,
                onBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Articles.route) {
            ArticlesScreen(
                onNavigateToAddArticle = {
                    navController.navigate(Screen.AddArticle.route)
                },
                onNavigateToEditArticle = { articleId ->
                    navController.navigate("${Screen.AddArticle.route}/$articleId")
                },
                onNavigateToReader = { articleId ->
                    navController.navigate("${Screen.Reader.route}/$articleId")
                },
                onNavigateToBottomNav = { route ->
                    navigateToRoute(navController, route)
                }
            )
        }

        composable(
            "${Screen.AddArticle.route}/{articleId}",
            arguments = listOf(navArgument("articleId") {
                type = NavType.LongType
                defaultValue = -1L
            })
        ) { backStackEntry ->
            val articleId = backStackEntry.arguments?.getLong("articleId") ?: -1L
            AddArticleScreen(
                articleId = if (articleId == -1L) null else articleId,
                onBack = { navController.popBackStack() }
            )
        }

        composable(Screen.AddArticle.route) {
            AddArticleScreen(
                articleId = null,
                onBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Stats.route) {
            StatsScreen(
                onNavigateToBottomNav = { route ->
                    navigateToRoute(navController, route)
                },
                onBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Settings.route) {
            SettingsScreen(
                onNavigateToBottomNav = { route ->
                    navigateToRoute(navController, route)
                },
                onBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Random.route) {
            RandomReadScreen(
                onNavigateToReader = { articleId ->
                    navController.navigate("${Screen.Reader.route}/$articleId")
                },
                onNavigateToBottomNav = { route ->
                    navigateToRoute(navController, route)
                }
            )
        }

        composable(Screen.Acupoint.route) {
            AcupointScreen(
                onNavigateToBottomNav = { route ->
                    navigateToRoute(navController, route)
                },
                onNavigateToManage = {
                    navController.navigate(Screen.AcupointManage.route)
                },
                onNavigateToEdit = { acupointId ->
                    navController.navigate("${Screen.AddAcupoint.route}/$acupointId")
                }
            )
        }

        composable(Screen.AcupointManage.route) {
            AcupointManageScreen(
                onNavigateToBottomNav = { route ->
                    navigateToRoute(navController, route)
                },
                onNavigateToAdd = {
                    navController.navigate(Screen.AddAcupoint.route)
                },
                onNavigateToEdit = { acupointId ->
                    navController.navigate("${Screen.AddAcupoint.route}/$acupointId")
                }
            )
        }

        composable(
            "${Screen.AddAcupoint.route}/{acupointId}",
            arguments = listOf(navArgument("acupointId") {
                type = NavType.LongType
                defaultValue = -1L
            })
        ) { backStackEntry ->
            val acupointId = backStackEntry.arguments?.getLong("acupointId") ?: -1L
            AddAcupointScreen(
                acupointId = if (acupointId == -1L) null else acupointId,
                onBack = { navController.popBackStack() }
            )
        }

        composable(Screen.AddAcupoint.route) {
            AddAcupointScreen(
                acupointId = null,
                onBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Concept.route) {
            ConceptScreen(
                onNavigateToBottomNav = { route ->
                    navigateToRoute(navController, route)
                },
                onNavigateToManage = {
                    navController.navigate(Screen.ConceptManage.route)
                },
                onNavigateToEdit = { conceptId ->
                    navController.navigate("${Screen.AddConcept.route}/$conceptId")
                }
            )
        }

        composable(Screen.ConceptManage.route) {
            ConceptManageScreen(
                onNavigateToBottomNav = { route ->
                    navigateToRoute(navController, route)
                },
                onNavigateToAdd = {
                    navController.navigate(Screen.AddConcept.route)
                },
                onNavigateToEdit = { conceptId ->
                    navController.navigate("${Screen.AddConcept.route}/$conceptId")
                }
            )
        }

        composable(
            "${Screen.AddConcept.route}/{conceptId}",
            arguments = listOf(navArgument("conceptId") {
                type = NavType.LongType
                defaultValue = -1L
            })
        ) { backStackEntry ->
            val conceptId = backStackEntry.arguments?.getLong("conceptId") ?: -1L
            AddConceptScreen(
                conceptId = if (conceptId == -1L) null else conceptId,
                onBack = { navController.popBackStack() }
            )
        }

        composable(Screen.AddConcept.route) {
            AddConceptScreen(
                conceptId = null,
                onBack = { navController.popBackStack() }
            )
        }
    }
}

private fun navigateToRoute(navController: NavHostController, route: String) {
    val currentRoute = navController.currentDestination?.route
    if (currentRoute == route) return
    
    when (route) {
        "home" -> {
            navController.navigate(Screen.Home.route) {
                popUpTo(Screen.Home.route) { inclusive = true }
            }
        }
        "articles" -> {
            navController.navigate(Screen.Articles.route) {
                popUpTo(Screen.Home.route)
            }
        }
        "random" -> {
            navController.navigate(Screen.Random.route) {
                popUpTo(Screen.Home.route)
            }
        }
        "acupoint" -> {
                navController.navigate(Screen.Acupoint.route) {
                    popUpTo(Screen.Home.route)
                }
            }
            "concept" -> {
                navController.navigate(Screen.Concept.route) {
                    popUpTo(Screen.Home.route)
                }
            }
            "settings" -> {
                navController.navigate(Screen.Settings.route) {
                    popUpTo(Screen.Home.route)
                }
            }
    }
}

sealed class Screen(val route: String) {
    object Home : Screen("home")
    object Reader : Screen("reader")
    object Articles : Screen("articles")
    object AddArticle : Screen("add_article")
    object Stats : Screen("stats")
    object Settings : Screen("settings")
    object Random : Screen("random")
    object Acupoint : Screen("acupoint")
    object AcupointManage : Screen("acupoint_manage")
    object AddAcupoint : Screen("add_acupoint")
    object Concept : Screen("concept")
    object ConceptManage : Screen("concept_manage")
    object AddConcept : Screen("add_concept")
}
