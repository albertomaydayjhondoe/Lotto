## 📝 Pull Request: [Title]

<!-- 
  ✅ BEFORE SUBMITTING: Complete the CHECKLIST OBLIGATORIO
  📚 Reference: docs/CHECKLIST_OBLIGATORIO.md
  🔍 This PR will be automatically validated by CI
-->

### 🎯 Purpose

<!-- Describe WHAT this PR does and WHY it's needed -->

**Type of Change:**
- [ ] 🐛 Bug fix
- [ ] ✨ New feature
- [ ] 🔧 Configuration change
- [ ] 📚 Documentation update
- [ ] ♻️ Code refactoring
- [ ] 🧪 Tests
- [ ] 🚀 Performance improvement
- [ ] 🔒 Security fix

**Related Issues:**
- Closes #[issue number]
- Relates to #[issue number]

---

### 📋 Changes Made

<!-- Provide a bullet-point list of the changes -->

- 
- 
- 

---

### 🧪 Testing

**Test Coverage:**
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All existing tests pass

**How to Test:**
```bash
# Steps to test this PR
pytest tests/test_<feature>.py -v
```

**Expected Behavior:**
<!-- Describe what should happen after these changes -->

---

### 📸 Screenshots (if applicable)

<!-- Add screenshots for UI changes -->

---

### 🔒 Security Checklist

- [ ] ✅ No secrets, API keys, or credentials exposed
- [ ] ✅ Input validation implemented
- [ ] ✅ Authentication/authorization checked
- [ ] ✅ SQL injection prevention verified
- [ ] ✅ XSS protection verified

---

### 📚 Documentation

- [ ] ✅ Code comments added where needed
- [ ] ✅ Docstrings updated
- [ ] ✅ README.md updated (if needed)
- [ ] ✅ CHANGELOG.md updated
- [ ] ✅ API documentation updated (if applicable)

---

### 🤖 AI/Prompt Changes (if applicable)

- [ ] N/A - No AI/prompt changes
- [ ] ✅ Prompt template versioned in `backend/app/prompts/`
- [ ] ✅ Prompt metadata includes `prompt_version`
- [ ] ✅ Response validation with Pydantic implemented
- [ ] ✅ Fallback mechanism implemented
- [ ] ✅ Token usage monitored
- [ ] ✅ Complies with `backend/app/prompts/PROMPT_REFINEMENT_CHECKLIST.md`

---

### 🔄 Database Changes (if applicable)

- [ ] N/A - No database changes
- [ ] ✅ Alembic migration created
- [ ] ✅ Migration has rollback
- [ ] ✅ Migration tested locally
- [ ] ✅ Indexes added where appropriate
- [ ] ✅ Foreign keys defined correctly

---

### ⚡ Performance Impact

<!-- Describe any performance implications -->

- [ ] ✅ No significant performance impact
- [ ] ⚠️ Performance impact assessed and acceptable
- [ ] 🚀 Performance improvement
- [ ] ⏱️ Requires performance testing

**Details:**
<!-- Add performance metrics, benchmarks, or considerations -->

---

### 🚨 Breaking Changes

- [ ] ✅ No breaking changes
- [ ] ⚠️ Breaking changes (describe below)

**Migration Path:**
<!-- If breaking changes, describe how to migrate -->

---

### 📦 Dependencies

- [ ] ✅ No new dependencies
- [ ] 📦 New dependencies added (list below)

**New Dependencies:**
<!-- List new packages and why they're needed -->
- `package-name==version` - Why it's needed

---

### ✅ Pre-Submission Checklist

- [ ] ✅ Code follows PEP 8 (flake8 passes)
- [ ] ✅ Type hints added
- [ ] ✅ Tests added and passing
- [ ] ✅ Documentation updated
- [ ] ✅ Commits are atomic and well-described
- [ ] ✅ Branch is up to date with target branch
- [ ] ✅ No merge conflicts
- [ ] ✅ Ran `python scripts/validate_checklist.py` successfully

---

### 👥 Reviewers

<!-- Tag specific reviewers if needed -->

**Requested Reviewers:**
- @sistemaproyectomunidal (if major change)
- @[team-member]

**Review Focus:**
<!-- Guide reviewers on what to focus on -->
- [ ] Code quality and architecture
- [ ] Security implications
- [ ] Performance considerations
- [ ] Test coverage
- [ ] Documentation completeness

---

### 🔗 Additional Context

<!-- Add any additional context, links, or information -->

**References:**
- [Design Document](link)
- [Related PR](link)
- [External Resource](link)

**Notes:**
<!-- Any additional notes for reviewers -->

---

### 📊 CI/CD Status

<!-- This will be automatically filled by GitHub Actions -->

The following checks will run automatically:
- ✅ Checklist Validation (`scripts/validate_checklist.py`)
- ✅ Security Scan (secrets detection)
- ✅ Linting (flake8, black, isort)
- ✅ Test Suite (pytest)

---

### 🎯 Post-Merge Actions

<!-- List any actions needed after merge -->

- [ ] Deploy to staging
- [ ] Update documentation site
- [ ] Notify stakeholders
- [ ] Monitor metrics
- [ ] Create follow-up issues

---

<!-- 
  ✨ Thank you for contributing to STAKAZO!
  
  📚 Resources:
  - Línea Maestra: docs/LINEA_MAESTRA_DESARROLLO.txt
  - Checklist: docs/CHECKLIST_OBLIGATORIO.md
  - Prompt Guidelines: backend/app/prompts/PROMPT_REFINEMENT_CHECKLIST.md
-->
