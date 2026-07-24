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

    signingConfigs {
        // Stabilný podpis: keystore je committed v repe (app/meteoduo-release.jks),
        // vygeneruje ho CI pri prvom builde. Vďaka tomu má každý release APK
        // rovnaký podpis → update sa nainštaluje „cez" starý bez odinštalovania.
        // (Pri hobby sideload appke je verejný keystore prijateľný kompromis.)
        create("release") {
            val ks = file("meteoduo-release.jks")
            if (ks.exists()) {
                storeFile = ks
                storePassword = "meteoduo"
                keyAlias = "meteoduo"
                keyPassword = "meteoduo"
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
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
