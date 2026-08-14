plugins {
    alias(libs.plugins.kotlin.jvm)
}

dependencies {
    implementation(project(":shared-protocol"))
    testImplementation(libs.junit)
}
