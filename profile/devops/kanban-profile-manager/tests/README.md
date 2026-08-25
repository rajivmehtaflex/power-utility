# Tests for kanban-profile-manager

## Running

```bash
cd ~/.hermes/skills/devops/kanban-profile-manager
pip install pyyaml pytest
python3 -m pytest tests/ -v
```

## Article test-case mapping

| Article test case | Test class | Test function |
|---|---|---|
| All profiles already exist | `TestReuseOnlyMode` | `test_all_exist_returns_reused` |
| One profile missing with approved template | `TestProvisionApprovedMode` | `test_creates_missing_profile` |
| Unknown role name | `TestUnknownRole` | `test_unregistered_role_is_blocked` |
| Profile exists but skills missing | (future) | `test_existing_profile_missing_skills` |
| Idempotency (run twice, no duplicates) | `TestIdempotency` | `test_second_run_does_not_recreate` |
| Phase 1 boundary enforcement | `TestPhaseOneBoundary` | `test_boundary_fields_enforced` |
| Empty registry edge case | `TestEmptyRegistry` | `test_empty_registry_produces_valid_report` |

## Task-driven mode tests (v2.1+)

| Capability | Test class | Test function |
|---|---|---|
| Role catalog contains all roles | `TestRoleCatalog` | `test_catalog_contains_all_roles` |
| Each catalog entry has capabilities | `TestRoleCatalog` | `test_catalog_includes_capabilities` |
| Catalog includes skills and auto_create | `TestRoleCatalog` | `test_catalog_includes_skills_and_auto_create` |
| Empty registry produces empty catalog | `TestRoleCatalog` | `test_empty_registry_catalog` |
| --roles flag checks only specified roles | `TestRolesFlag` | `test_specific_roles_checked` |
| Mixed known + unknown roles handled | `TestRolesFlag` | `test_mixed_known_and_unknown_roles` |

## Config override tests (v3.0+)

| Capability | Test file | Test class / function |
|---|---|---|
| Scalar override | `test_config_merger.py` | `TestDeepMerge::test_scalar_override` |
| Nested dict merge | `test_config_merger.py` | `TestDeepMerge::test_nested_dict_merge` |
| List replaced not merged | `test_config_merger.py` | `TestDeepMerge::test_list_replaced_not_merged` |
| Model key never touched | `test_config_merger.py` | `TestDeepMerge::test_model_key_never_touched` |
| Providers key never touched | `test_config_merger.py` | `TestDeepMerge::test_providers_key_never_touched` |
| New key added | `test_config_merger.py` | `TestDeepMerge::test_new_key_added` |
| Inputs not mutated | `test_config_merger.py` | `TestDeepMerge::test_does_not_mutate_inputs` |
| Warns on model key | `test_config_merger.py` | `TestValidateOverrides::test_warns_on_model_key` |
| No warnings for safe keys | `test_config_merger.py` | `TestValidateOverrides::test_no_warnings_for_safe_keys` |
| Warns on all protected keys | `test_config_merger.py` | `TestValidateOverrides::test_warns_on_all_protected_keys` |
| Writes merged config to disk | `test_config_merger.py` | `TestApplyOverridesToConfig::test_writes_merged_config` |
| Model preserved after apply | `test_config_merger.py` | `TestApplyOverridesToConfig::test_model_preserved_after_apply` |
| Raises on missing file | `test_config_merger.py` | `TestApplyOverridesToConfig::test_raises_on_missing_file` |
| Overrides applied on provision | `test_profile_check.py` | `TestConfigOverrides::test_overrides_applied_on_provision` |
| No overrides when no config block | `test_profile_check.py` | `TestConfigOverrides::test_no_overrides_when_no_config_block` |
| Model never in fixture overrides | `test_profile_check.py` | `TestConfigOverrides::test_model_never_in_fixture_overrides` |
| --no-config flag skips overrides | `test_profile_check.py` | `TestConfigOverrides::test_no_config_flag_skips_overrides` |

All tests use mocked subprocess calls — no live Hermes installation or real
profile mutations are needed.
