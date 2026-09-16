#!/usr/bin/env python3
"""Generates Barkly.xcodeproj (project.pbxproj + shared scheme) for the BARKLY app.

Run from the repo root:
    python3 Scripts/generate_project.py

The generator discovers every Swift file under Barkly/ and BarklyTests/ so the
project always stays in sync with the source tree.
"""
import hashlib
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, "Barkly")
TESTS = os.path.join(REPO, "BarklyTests")
XCODEPROJ = os.path.join(REPO, "Barkly.xcodeproj")
DEPLOYMENT = "17.0"


BUNDLE_ID = "com.barkly.app"
TEST_BUNDLE_ID = "com.barkly.app.tests"
MIC_DESC = "BARKLY uses the microphone when you record your dog's sounds for behavioral analysis."
PHOTO_DESC = "BARKLY uses your photo library when you choose to analyze a dog video or photo."


def ident(seed):
    return hashlib.md5(seed.encode()).hexdigest()[:24].upper()


def discover():
    swift_files, assetcatalogs = [], []
    for base in (ROOT, TESTS):
        for dirpath, dirnames, filenames in os.walk(base):
            if os.path.basename(dirpath) == "Assets.xcassets":
                assetcatalogs.append(os.path.relpath(dirpath, REPO))
                dirnames[:] = []
            for name in filenames:
                if name.endswith(".swift"):
                    rel = os.path.relpath(os.path.join(dirpath, name), REPO)
                    swift_files.append(rel)
    swift_files.sort()
    assetcatalogs.sort()
    return swift_files, assetcatalogs


def q(value):
    return value if all(c.isalnum() or c in "._-/" for c in value) else '"{}"'.format(value)


def is_swift(rel):
    return rel.endswith(".swift")


def project_configs(mode):
    common = {
        "ALWAYS_SEARCH_USER_PATHS": "NO",
        "CLANG_ENABLE_MODULES": "YES",
        "CLANG_ENABLE_OBJC_ARC": "YES",
        "CLANG_WARN_BOOL_CONVERSION": "YES",
        "CLANG_WARN_CONSTANT_CONVERSION": "YES",
        "CLANG_WARN_EMPTY_BODY": "YES",
        "CLANG_WARN_ENUM_CONVERSION": "YES",
        "CLANG_WARN_INFINITE_RECURSION": "YES",
        "CLANG_WARN_INT_CONVERSION": "YES",
        "CLANG_WARN_UNREACHABLE_CODE": "YES",
        "COPY_PHASE_STRIP": "NO",
        "GCC_C_LANGUAGE_STANDARD": "gnu17",
        "GCC_NO_COMMON_BLOCKS": "YES",
        "IPHONEOS_DEPLOYMENT_TARGET": DEPLOYMENT,
        "SDKROOT": "iphoneos",
        "SWIFT_VERSION": "5.0",
        "ENABLE_STRICT_OBJC_MSGSEND": "YES",
    }
    if mode == "Debug":
        common.update({
            "DEBUG_INFORMATION_FORMAT": "dwarf",
            "ENABLE_TESTABILITY": "YES",
            "GCC_OPTIMIZATION_LEVEL": "0",
            "GCC_PREPROCESSOR_DEFINITIONS": '("DEBUG=1", "$(inherited)")',
            "ONLY_ACTIVE_ARCH": "YES",
            "SWIFT_ACTIVE_COMPILATION_CONDITIONS": "DEBUG $(inherited)",
            "SWIFT_OPTIMIZATION_LEVEL": "-Onone",
            "MTL_ENABLE_DEBUG_INFO": "INCLUDE_SOURCE",
        })
    else:
        common.update({
            "DEBUG_INFORMATION_FORMAT": "dwarf-with-dsym",
            "ENABLE_NS_ASSERTIONS": "NO",
            "ONLY_ACTIVE_ARCH": "NO",
            "SWIFT_COMPILATION_MODE": "wholemodule",
            "SWIFT_OPTIMIZATION_LEVEL": "-O",
            "SWIFT_ACTIVE_COMPILATION_CONDITIONS": "$(inherited)",
            "COPY_PHASE_STRIP": "YES",
        })
    return common


def app_configs(mode):
    common = {
        "ASSETCATALOG_COMPILER_APPICON_NAME": "AppIcon",
        "ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME": "AccentColor",
        "CODE_SIGN_STYLE": "Automatic",
        "CURRENT_PROJECT_VERSION": "1",
        "ENABLE_PREVIEWS": "YES",
        "GENERATE_INFOPLIST_FILE": "YES",
        "INFOPLIST_KEY_NSAppTransportSecurity_NSAllowsLocalNetworking": "YES",
        "INFOPLIST_KEY_NSMicrophoneUsageDescription": MIC_DESC,
        "INFOPLIST_KEY_NSPhotoLibraryUsageDescription": PHOTO_DESC,
        "INFOPLIST_KEY_UIApplicationSceneManifest_Generation": "YES",
        "INFOPLIST_KEY_UIApplicationSupportsIndirectInputEvents": "YES",
        "INFOPLIST_KEY_UILaunchScreen_Generation": "YES",
        "LD_RUNPATH_SEARCH_PATHS": '("$(inherited)", "@executable_path/Frameworks")',
        "MARKETING_VERSION": "1.0",
        "PRODUCT_BUNDLE_IDENTIFIER": BUNDLE_ID,
        "PRODUCT_NAME": "$(TARGET_NAME)",
        "SWIFT_EMIT_LOC_STRINGS": "YES",
        "TARGETED_DEVICE_FAMILY": "1,2",
    }
    out = project_configs(mode)
    out.update(common)
    return out


def test_configs(mode):
    common = {
        "BUNDLE_LOADER": "$(TEST_HOST)",
        "CODE_SIGN_STYLE": "Automatic",
        "CURRENT_PROJECT_VERSION": "1",
        "GENERATE_INFOPLIST_FILE": "YES",
        "IPHONEOS_DEPLOYMENT_TARGET": DEPLOYMENT,
        "MARKETING_VERSION": "1.0",
        "PRODUCT_BUNDLE_IDENTIFIER": TEST_BUNDLE_ID,
        "PRODUCT_NAME": "$(TARGET_NAME)",
        "SWIFT_EMIT_LOC_STRINGS": "NO",
        "TARGETED_DEVICE_FAMILY": "1,2",
        "TEST_HOST": "$(BUILT_PRODUCTS_DIR)/Barkly.app/Barkly",
    }
    out = project_configs(mode)
    out.update(common)
    return out


def emit_value(v):
    if v.startswith("(") and v.endswith(")"):
        return v
    return q(v)


def pbx_build_settings(entries, indent="\t\t\t"):
    return "\n".join("{} {} = {};".format(indent, k, emit_value(v)) for k, v in entries.items())


def main():
    swift_files, assets = discover()

    app_sources = [rel for rel in swift_files if rel.startswith("Barkly/")]
    test_sources = [rel for rel in swift_files if rel.startswith("BarklyTests/")]
    resource_files = assets

    assert app_sources, "no app sources found"

    gid_main = ident("group:.")
    gid_products = ident("group:Products")
    gid_app_root = ident("group:Barkly")
    gid_test_root = ident("group:BarklyTests")

    app_prod_fid = ident("prod:Barkly.app")
    test_prod_fid = ident("prod:BarklyTests.xctest")

    file_refs = {}
    for rel in app_sources + test_sources + resource_files:
        file_refs[rel] = ident("file:" + rel)

    # Build nested groups from relative dirs.
    group_path = {gid_main: "", gid_products: "Products", gid_app_root: "Barkly", gid_test_root: "BarklyTests"}
    rel_gid = {"Barkly": gid_app_root, "BarklyTests": gid_test_root}
    group_children = {}
    group_children[gid_main] = [(0, gid_app_root, "Barkly"), (0, gid_test_root, "BarklyTests"), (0, gid_products, "Products")]
    group_children[gid_products] = [(1, app_prod_fid, "Barkly.app"), (1, test_prod_fid, "BarklyTests.xctest")]
    group_children[gid_app_root] = []
    group_children[gid_test_root] = []

    def get_group(rel_dir):
        if rel_dir in rel_gid:
            return rel_gid[rel_dir]
        parent_rel = os.path.dirname(rel_dir)
        parent_gid = get_group(parent_rel)
        gid = ident("group:" + rel_dir)
        rel_gid[rel_dir] = gid
        group_path[gid] = rel_dir
        group_children[gid] = []
        group_children[parent_gid].append((0, gid, os.path.basename(rel_dir)))
        return gid

    for rel in app_sources + resource_files:
        rel_dir = os.path.dirname(rel)
        get_group(rel_dir)
    for rel in test_sources:
        rel_dir = os.path.dirname(rel)
        get_group(rel_dir)

    for rel in app_sources + test_sources + resource_files:
        rel_dir = os.path.dirname(rel)
        gid = get_group(rel_dir)
        group_children[gid].append((1, file_refs[rel], os.path.basename(rel)))

    # Target ids
    tid_app = ident("target:Barkly")
    tid_tests = ident("target:BarklyTests")
    phase_sources_app = ident("sources:app")
    phase_frameworks_app = ident("frameworks:app")
    phase_resources_app = ident("resources:app")
    phase_sources_tests = ident("sources:tests")
    phase_frameworks_tests = ident("frameworks:tests")
    phase_resources_tests = ident("resources:tests")

    cfg_proj_debug = ident("cfg:proj:Debug")
    cfg_proj_release = ident("cfg:proj:Release")
    cfg_app_debug = ident("cfg:app:Debug")
    cfg_app_release = ident("cfg:app:Release")
    cfg_test_debug = ident("cfg:test:Debug")
    cfg_test_release = ident("cfg:test:Release")
    cfglist_proj = ident("cfglist:proj")
    cfglist_app = ident("cfglist:app")
    cfglist_test = ident("cfglist:test")

    build_files_app = []
    build_files_tests = []
    build_files_res = []

    project_ref = ident("project")

    lines = []
    lines.append("// !$*UTF8*$!")
    lines.append("{")
    lines.append("\tarchiveVersion = 1;")
    lines.append("\tclasses = {")
    lines.append("\t};")
    lines.append("\tobjectVersion = 56;")
    lines.append("\tobjects = {")

    # PBXBuildFile
    lines.append("")
    lines.append("\t/* Begin PBXBuildFile section */")
    for rel in app_sources:
        fid = file_refs[rel]
        bid = ident("build:app:" + rel)
        lines.append("\t\t{} /* {} in Sources */ = {{isa = PBXBuildFile; fileRef = {} /* {} */; }};".format(bid, os.path.basename(rel), fid, os.path.basename(rel)))
        build_files_app.append(bid)
    for rel in test_sources:
        fid = file_refs[rel]
        bid = ident("build:tests:" + rel)
        lines.append("\t\t{} /* {} in Sources */ = {{isa = PBXBuildFile; fileRef = {} /* {} */; }};".format(bid, os.path.basename(rel), fid, os.path.basename(rel)))
        build_files_tests.append(bid)
    for rel in resource_files:
        fid = file_refs[rel]
        bid = ident("build:res:" + rel)
        lines.append("\t\t{} /* {} in Resources */ = {{isa = PBXBuildFile; fileRef = {} /* {} */; }};".format(bid, os.path.basename(os.path.dirname(rel)), fid, os.path.basename(os.path.dirname(rel))))
        build_files_res.append(bid)
    lines.append("\t/* End PBXBuildFile section */")

    # PBXContainerItemProxy
    lines.append("")
    lines.append("\t/* Begin PBXContainerItemProxy section */")
    proxy = ident("proxy:tests")
    dep = ident("dep:tests")
    lines.append("\t\t{} /* PBXContainerItemProxy */ = {{isa = PBXContainerItemProxy; containerPortal = {} /* Project object */; proxyType = 1; remoteGlobalIDString = {}; remoteInfo = Barkly; }};".format(proxy, project_ref, tid_app))
    lines.append("\t/* End PBXContainerItemProxy section */")

    # PBXFileReference
    lines.append("")
    lines.append("\t/* Begin PBXFileReference section */")
    lines.append("\t\t{} /* Barkly.app */ = {{isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = Barkly.app; sourceTree = BUILT_PRODUCTS_DIR; }};".format(app_prod_fid))
    lines.append("\t\t{} /* BarklyTests.xctest */ = {{isa = PBXFileReference; explicitFileType = wrapper.cfbundle; includeInIndex = 0; path = BarklyTests.xctest; sourceTree = BUILT_PRODUCTS_DIR; }};".format(test_prod_fid))
    for rel in sorted(file_refs):
        fid = file_refs[rel]
        name = os.path.basename(rel)
        if rel in resource_files:
            lines.append("\t\t{} /* {} */ = {{isa = PBXFileReference; lastKnownFileType = folder.assetcatalog; name = {}; path = {}; sourceTree = \"<group>\"; }};".format(fid, name, q(name), q(name)))
        else:
            lines.append("\t\t{} /* {} */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = {}; sourceTree = \"<group>\"; }};".format(fid, name, q(name)))
    lines.append("\t/* End PBXFileReference section */")

    # PBXFrameworksBuildPhase
    lines.append("")
    lines.append("\t/* Begin PBXFrameworksBuildPhase section */")
    lines.append("\t\t{} /* Frameworks */ = {{isa = PBXFrameworksBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; }};".format(phase_frameworks_app))
    lines.append("\t\t{} /* Frameworks */ = {{isa = PBXFrameworksBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; }};".format(phase_frameworks_tests))
    lines.append("\t/* End PBXFrameworksBuildPhase section */")

    # PBXGroup
    lines.append("")
    lines.append("\t/* Begin PBXGroup section */")
    all_groups = {}
    all_groups[gid_main] = ("", "")
    all_groups[gid_products] = ("Products", "Products")
    all_groups[gid_app_root] = ("Barkly", "Barkly")
    all_groups[gid_test_root] = ("BarklyTests", "BarklyTests")
    for gid, rel_dir in sorted(group_path.items()):
        if gid in all_groups:
            continue
        all_groups[gid] = (os.path.basename(rel_dir) or rel_dir, os.path.basename(rel_dir) or rel_dir)

    for gid, (name, path) in sorted(all_groups.items()):
        children = group_children.get(gid, [])
        child_parts = []
        for kind, cid, cname in children:
            child_parts.append("{} /* {} */".format(cid, cname))
        child_str = ", ".join(child_parts)
        if child_str:
            child_str = "(" + child_str + ")"
        else:
            child_str = "()"
        if path == "":
            lines.append("\t\t{} = {{isa = PBXGroup; children = {}; sourceTree = \"<group>\"; }};".format(gid, child_str))
        elif gid == gid_products:
            lines.append("\t\t{} /* {} */ = {{isa = PBXGroup; children = {}; name = {}; sourceTree = \"<group>\"; }};".format(gid, name, child_str, q(name)))
        else:
            lines.append("\t\t{} /* {} */ = {{isa = PBXGroup; children = {}; path = {}; sourceTree = \"<group>\"; }};".format(gid, name, child_str, q(path)))
    lines.append("\t/* End PBXGroup section */")

    # PBXNativeTarget
    lines.append("")
    lines.append("\t/* Begin PBXNativeTarget section */")
    lines.append("\t\t{} /* Barkly */ = {{isa = PBXNativeTarget; buildConfigurationList = {} /* Build configuration list for PBXNativeTarget \"Barkly\" */; buildPhases = ({} /* Sources */, {} /* Frameworks */, {} /* Resources */); buildRules = (); dependencies = (); name = Barkly; productName = Barkly; productReference = {} /* Barkly.app */; productType = \"com.apple.product-type.application\"; }};".format(tid_app, cfglist_app, phase_sources_app, phase_frameworks_app, phase_resources_app, app_prod_fid))
    lines.append("\t\t{} /* BarklyTests */ = {{isa = PBXNativeTarget; buildConfigurationList = {} /* Build configuration list for PBXNativeTarget \"BarklyTests\" */; buildPhases = ({} /* Sources */, {} /* Frameworks */, {} /* Resources */); buildRules = (); dependencies = ({} /* PBXTargetDependency */); name = BarklyTests; productName = BarklyTests; productReference = {} /* BarklyTests.xctest */; productType = \"com.apple.product-type.bundle.unit-test\"; }};".format(tid_tests, cfglist_test, phase_sources_tests, phase_frameworks_tests, phase_resources_tests, dep, test_prod_fid))
    lines.append("\t/* End PBXNativeTarget section */")

    # PBXProject
    lines.append("")
    lines.append("\t/* Begin PBXProject section */")
    lines.append("\t\t{} /* Project object */ = {{isa = PBXProject; attributes = {{BuildIndependentTargetsInParallel = 1; LastSwiftUpdateCheck = 2600; LastUpgradeCheck = 2600; TargetAttributes = {{ {} = {{CreatedOnToolsVersion = 26.0; }}; {} = {{CreatedOnToolsVersion = 26.0; TestTargetID = {}; }}; }}; }}; buildConfigurationList = {} /* Build configuration list for PBXProject \"Barkly\" */; compatibilityVersion = \"Xcode 14.0\"; developmentRegion = en; hasScannedForEncodings = 0; knownRegions = (en, Base); mainGroup = {}; productRefGroup = {} /* Products */; projectDirPath = \"\"; projectRoot = \"\"; targets = ({} /* Barkly */, {} /* BarklyTests */); }};".format(project_ref, tid_app, tid_tests, tid_app, cfglist_proj, gid_main, gid_products, tid_app, tid_tests))
    lines.append("\t/* End PBXProject section */")

    # PBXResourcesBuildPhase
    lines.append("")
    lines.append("\t/* Begin PBXResourcesBuildPhase section */")
    res_files_app = build_files_res
    lines.append("\t\t{} /* Resources */ = {{isa = PBXResourcesBuildPhase; buildActionMask = 2147483647; files = ({}); runOnlyForDeploymentPostprocessing = 0; }};".format(phase_resources_app, ", ".join(res_files_app)))
    lines.append("\t\t{} /* Resources */ = {{isa = PBXResourcesBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; }};".format(phase_resources_tests))
    lines.append("\t/* End PBXResourcesBuildPhase section */")

    # PBXSourcesBuildPhase
    lines.append("")
    lines.append("\t/* Begin PBXSourcesBuildPhase section */")
    lines.append("\t\t{} /* Sources */ = {{isa = PBXSourcesBuildPhase; buildActionMask = 2147483647; files = ({}); runOnlyForDeploymentPostprocessing = 0; }};".format(phase_sources_app, ", ".join(build_files_app)))
    lines.append("\t\t{} /* Sources */ = {{isa = PBXSourcesBuildPhase; buildActionMask = 2147483647; files = ({}); runOnlyForDeploymentPostprocessing = 0; }};".format(phase_sources_tests, ", ".join(build_files_tests)))
    lines.append("\t/* End PBXSourcesBuildPhase section */")

    # PBXTargetDependency
    lines.append("")
    lines.append("\t/* Begin PBXTargetDependency section */")
    lines.append("\t\t{} /* PBXTargetDependency */ = {{isa = PBXTargetDependency; target = {} /* Barkly */; targetProxy = {} /* PBXContainerItemProxy */; }};".format(dep, tid_app, proxy))
    lines.append("\t/* End PBXTargetDependency section */")

    # XCBuildConfiguration
    def emit_config(cid, name, target_name, settings):
        lines.append("\t\t{} /* {} */ = {{isa = XCBuildConfiguration; buildSettings = {{".format(cid, name))
        inset = pbx_build_settings(settings, "\t\t\t\t")
        lines.append(inset)
        lines.append("\t\t\t}}; name = {}; }};".format(name))

    lines.append("")
    lines.append("\t/* Begin XCBuildConfiguration section */")
    emit_config(cfg_proj_debug, "Debug", "Project", project_configs("Debug"))
    emit_config(cfg_proj_release, "Release", "Project", project_configs("Release"))
    emit_config(cfg_app_debug, "Debug", "Barkly", app_configs("Debug"))
    emit_config(cfg_app_release, "Release", "Barkly", app_configs("Release"))
    emit_config(cfg_test_debug, "Debug", "BarklyTests", test_configs("Debug"))
    emit_config(cfg_test_release, "Release", "BarklyTests", test_configs("Release"))
    lines.append("\t/* End XCBuildConfiguration section */")

    # XCConfigurationList
    lines.append("")
    lines.append("\t/* Begin XCConfigurationList section */")
    lines.append("\t\t{} /* Build configuration list for PBXProject \"Barkly\" */ = {{isa = XCConfigurationList; buildConfigurations = ({} /* Debug */, {} /* Release */); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release; }};".format(cfglist_proj, cfg_proj_debug, cfg_proj_release))
    lines.append("\t\t{} /* Build configuration list for PBXNativeTarget \"Barkly\" */ = {{isa = XCConfigurationList; buildConfigurations = ({} /* Debug */, {} /* Release */); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release; }};".format(cfglist_app, cfg_app_debug, cfg_app_release))
    lines.append("\t\t{} /* Build configuration list for PBXNativeTarget \"BarklyTests\" */ = {{isa = XCConfigurationList; buildConfigurations = ({} /* Debug */, {} /* Release */); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release; }};".format(cfglist_test, cfg_test_debug, cfg_test_release))
    lines.append("\t/* End XCConfigurationList section */")

    lines.append("\t};")
    lines.append("\trootObject = {} /* Project object */;".format(project_ref))
    lines.append("}")

    os.makedirs(XCODEPROJ, exist_ok=True)
    with open(os.path.join(XCODEPROJ, "project.pbxproj"), "w") as f:
        f.write("\n".join(lines) + "\n")

    scheme_dir = os.path.join(XCODEPROJ, "xcshareddata", "xcschemes")
    os.makedirs(scheme_dir, exist_ok=True)
    scheme = SCHEME_TEMPLATE.replace("{APP_ID}", tid_app).replace("{TEST_ID}", tid_tests).replace("{PROXY_ID}", proxy)
    with open(os.path.join(scheme_dir, "Barkly.xcscheme"), "w") as f:
        f.write(scheme)

    print("Wrote Barkly.xcodeproj")
    print("  app sources:  ", len(app_sources))
    print("  test sources: ", len(test_sources))
    print("  resources:    ", len(resource_files))


SCHEME_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<Scheme
   LastUpgradeVersion = "2600"
   version = "1.7">
   <BuildAction
      parallelizeBuildables = "YES"
      buildImplicitDependencies = "YES">
      <BuildActionEntries>
         <BuildActionEntry
            buildForTesting = "YES"
            buildForRunning = "YES"
            buildForProfiling = "YES"
            buildForArchiving = "YES"
            buildForAnalyzing = "YES">
            <BuildableReference
               BuildableIdentifier = "primary"
               BlueprintIdentifier = "{APP_ID}"
               BuildableName = "Barkly.app"
               BlueprintName = "Barkly"
               ReferencedContainer = "container:Barkly.xcodeproj">
            </BuildableReference>
         </BuildActionEntry>
         <BuildActionEntry
            buildForTesting = "YES"
            buildForRunning = "YES"
            buildForProfiling = "NO"
            buildForArchiving = "NO"
            buildForAnalyzing = "YES">
            <BuildableReference
               BuildableIdentifier = "primary"
               BlueprintIdentifier = "{TEST_ID}"
               BuildableName = "BarklyTests.xctest"
               BlueprintName = "BarklyTests"
               ReferencedContainer = "container:Barkly.xcodeproj">
            </BuildableReference>
         </BuildActionEntry>
      </BuildActionEntries>
   </BuildAction>
   <TestAction
      buildConfiguration = "Debug"
      selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB"
      selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB"
      shouldUseLaunchSchemeArgsEnv = "YES"
      shouldAutocreateTestPlan = "YES">
      <Testables>
         <TestableReference
            skipped = "NO">
            <BuildableReference
               BuildableIdentifier = "primary"
               BlueprintIdentifier = "{TEST_ID}"
               BuildableName = "BarklyTests.xctest"
               BlueprintName = "BarklyTests"
               ReferencedContainer = "container:Barkly.xcodeproj">
            </BuildableReference>
         </TestableReference>
      </Testables>
   </TestAction>
   <LaunchAction
      buildConfiguration = "Debug"
      selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB"
      selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB"
      launchStyle = "0"
      useCustomWorkingDirectory = "NO"
      ignoresPersistentStateOnLaunch = "NO"
      debugDocumentVersioning = "YES"
      debugServiceExtension = "internal"
      allowLocationSimulation = "YES">
      <BuildableProductRunnable
         runnableDebuggingMode = "0">
         <BuildableReference
            BuildableIdentifier = "primary"
            BlueprintIdentifier = "{APP_ID}"
            BuildableName = "Barkly.app"
            BlueprintName = "Barkly"
            ReferencedContainer = "container:Barkly.xcodeproj">
         </BuildableReference>
      </BuildableProductRunnable>
   </LaunchAction>
   <ProfileAction
      buildConfiguration = "Release"
      shouldUseLaunchSchemeArgsEnv = "YES"
      savedToolIdentifier = ""
      useCustomWorkingDirectory = "NO"
      debugDocumentVersioning = "YES">
      <BuildableProductRunnable
         runnableDebuggingMode = "0">
         <BuildableReference
            BuildableIdentifier = "primary"
            BlueprintIdentifier = "{APP_ID}"
            BuildableName = "Barkly.app"
            BlueprintName = "Barkly"
            ReferencedContainer = "container:Barkly.xcodeproj">
         </BuildableReference>
      </BuildableProductRunnable>
   </ProfileAction>
   <AnalyzeAction
      buildConfiguration = "Debug">
   </AnalyzeAction>
   <ArchiveAction
      buildConfiguration = "Release"
      revealArchiveInOrganizer = "YES">
   </ArchiveAction>
</Scheme>
"""


if __name__ == "__main__":
    main()