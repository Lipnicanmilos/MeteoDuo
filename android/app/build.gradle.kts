plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "sk.meteoduo.widget"
    compileSdk = 34

    defaultConfig {
        applicationId = "sk.meteoduo.widget"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    // Zámerne minimálne — RemoteViews, HttpURLConnection aj org.json sú v SDK,
    // takže žiadny appcompat/material netreba.
    implementation("androidx.core:core-ktx:1.13.1")
}
