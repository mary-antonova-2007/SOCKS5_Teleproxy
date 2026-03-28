(function () {
  const storageKey = "ts5_admin_session";
  const state = {
    token: "",
    username: "",
    role: "",
    users: [],
    editingUser: null,
    deletingUser: null,
  };

  const elements = {
    loginView: document.getElementById("loginView"),
    dashboardView: document.getElementById("dashboardView"),
    loginForm: document.getElementById("loginForm"),
    loginButton: document.getElementById("loginButton"),
    loginError: document.getElementById("loginError"),
    welcomeText: document.getElementById("welcomeText"),
    roleBadge: document.getElementById("roleBadge"),
    logoutButton: document.getElementById("logoutButton"),
    createUserButton: document.getElementById("createUserButton"),
    refreshButton: document.getElementById("refreshButton"),
    usersGrid: document.getElementById("usersGrid"),
    usersCount: document.getElementById("usersCount"),
    emptyState: document.getElementById("emptyState"),
    userCardTemplate: document.getElementById("userCardTemplate"),
    userModal: document.getElementById("userModal"),
    userModalTitle: document.getElementById("userModalTitle"),
    userModalEyebrow: document.getElementById("userModalEyebrow"),
    userForm: document.getElementById("userForm"),
    userFormHint: document.getElementById("userFormHint"),
    userFormError: document.getElementById("userFormError"),
    modalUsername: document.getElementById("modalUsername"),
    modalPassword: document.getElementById("modalPassword"),
    modalEnabled: document.getElementById("modalEnabled"),
    saveUserButton: document.getElementById("saveUserButton"),
    closeUserModal: document.getElementById("closeUserModal"),
    cancelUserModal: document.getElementById("cancelUserModal"),
    deleteModal: document.getElementById("deleteModal"),
    deleteUsername: document.getElementById("deleteUsername"),
    deleteError: document.getElementById("deleteError"),
    closeDeleteModal: document.getElementById("closeDeleteModal"),
    cancelDeleteModal: document.getElementById("cancelDeleteModal"),
    confirmDeleteButton: document.getElementById("confirmDeleteButton"),
  };

  function setSession(session) {
    state.token = session.access_token || "";
    state.username = session.username || "";
    state.role = session.role || "";
    localStorage.setItem(
      storageKey,
      JSON.stringify({
        access_token: state.token,
        username: state.username,
        role: state.role,
      }),
    );
  }

  function clearSession() {
    state.token = "";
    state.username = "";
    state.role = "";
    localStorage.removeItem(storageKey);
  }

  function restoreSession() {
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) {
        return false;
      }
      const parsed = JSON.parse(raw);
      if (!parsed.access_token || !parsed.username) {
        return false;
      }
      state.token = parsed.access_token;
      state.username = parsed.username;
      state.role = parsed.role || "admin";
      return true;
    } catch (_error) {
      clearSession();
      return false;
    }
  }

  async function api(path, options = {}) {
    const config = {
      method: options.method || "GET",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    };

    if (state.token) {
      config.headers.Authorization = `Bearer ${state.token}`;
    }
    if (options.body !== undefined) {
      config.body = JSON.stringify(options.body);
    }

    const response = await fetch(path, config);
    if (response.status === 401) {
      clearSession();
      showLogin();
      throw new Error("Сессия истекла. Войдите заново.");
    }

    const text = await response.text();
    const payload = text ? JSON.parse(text) : {};
    if (!response.ok) {
      throw new Error(payload.detail || "Не удалось выполнить запрос");
    }
    return payload;
  }

  function showLogin() {
    elements.loginView.classList.remove("hidden");
    elements.dashboardView.classList.add("hidden");
    closeUserModal();
    closeDeleteModal();
  }

  function showDashboard() {
    elements.loginView.classList.add("hidden");
    elements.dashboardView.classList.remove("hidden");
    elements.welcomeText.textContent = `Привет, ${state.username}`;
    elements.roleBadge.textContent = state.role;
  }

  function formatDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return new Intl.DateTimeFormat("ru-RU", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(date);
  }

  function renderUsers() {
    elements.usersGrid.innerHTML = "";
    elements.usersCount.textContent = `${state.users.length} ${pluralizeUsers(state.users.length)}`;
    elements.emptyState.classList.toggle("hidden", state.users.length > 0);

    state.users.forEach((user) => {
      const node = elements.userCardTemplate.content.firstElementChild.cloneNode(true);
      node.querySelector(".user-name").textContent = user.username;
      node.querySelector(".user-meta").textContent = user.enabled ? "Активный доступ к прокси" : "Доступ временно отключён";

      const status = node.querySelector(".status-pill");
      status.textContent = user.enabled ? "Активен" : "Отключён";
      status.classList.toggle("is-disabled", !user.enabled);

      node.querySelector(".timestamps").textContent = `Создан: ${formatDate(user.created_at)} | Обновлён: ${formatDate(user.updated_at)}`;

      node.querySelector(".edit-user").addEventListener("click", () => openEditModal(user));
      node.querySelector(".delete-user").addEventListener("click", () => openDeleteModal(user));
      elements.usersGrid.appendChild(node);
    });
  }

  function pluralizeUsers(count) {
    const mod10 = count % 10;
    const mod100 = count % 100;
    if (mod10 === 1 && mod100 !== 11) {
      return "пользователь";
    }
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
      return "пользователя";
    }
    return "пользователей";
  }

  async function loadUsers() {
    const users = await api("/proxy-users");
    state.users = users;
    renderUsers();
  }

  function resetUserForm() {
    elements.userForm.reset();
    elements.userFormError.textContent = "";
    elements.userFormHint.textContent = "";
  }

  function openCreateModal() {
    state.editingUser = null;
    resetUserForm();
    elements.userModalTitle.textContent = "Создать пользователя";
    elements.userModalEyebrow.textContent = "Новый пользователь";
    elements.saveUserButton.textContent = "Создать";
    elements.modalUsername.disabled = false;
    elements.modalPassword.required = true;
    elements.userFormHint.textContent = "Имя пользователя должно быть уникальным. Пароль сразу попадёт в конфигурацию прокси.";
    elements.userModal.classList.remove("hidden");
    elements.modalUsername.focus();
  }

  function openEditModal(user) {
    state.editingUser = user;
    resetUserForm();
    elements.userModalTitle.textContent = `Редактировать ${user.username}`;
    elements.userModalEyebrow.textContent = "Редактирование";
    elements.saveUserButton.textContent = "Сохранить";
    elements.modalUsername.value = user.username;
    elements.modalUsername.disabled = true;
    elements.modalPassword.required = false;
    elements.modalPassword.placeholder = "Оставьте пустым, чтобы не менять пароль";
    elements.modalEnabled.checked = user.enabled;
    elements.userFormHint.textContent = "Можно изменить пароль и состояние доступа. Логин остаётся неизменным.";
    elements.userModal.classList.remove("hidden");
    elements.modalPassword.focus();
  }

  function closeUserModal() {
    elements.userModal.classList.add("hidden");
    state.editingUser = null;
  }

  function openDeleteModal(user) {
    state.deletingUser = user;
    elements.deleteError.textContent = "";
    elements.deleteUsername.textContent = user.username;
    elements.deleteModal.classList.remove("hidden");
  }

  function closeDeleteModal() {
    elements.deleteModal.classList.add("hidden");
    state.deletingUser = null;
  }

  async function handleLogin(event) {
    event.preventDefault();
    elements.loginError.textContent = "";
    elements.loginButton.disabled = true;
    elements.loginButton.textContent = "Проверяем...";

    const formData = new FormData(elements.loginForm);
    try {
      const session = await api("/auth/login", {
        method: "POST",
        body: {
          username: formData.get("username"),
          password: formData.get("password"),
        },
      });
      setSession(session);
      showDashboard();
      await loadUsers();
      elements.loginForm.reset();
    } catch (error) {
      elements.loginError.textContent = error.message;
    } finally {
      elements.loginButton.disabled = false;
      elements.loginButton.textContent = "Войти";
    }
  }

  async function handleSaveUser(event) {
    event.preventDefault();
    elements.userFormError.textContent = "";

    const username = elements.modalUsername.value.trim();
    const password = elements.modalPassword.value;
    const enabled = elements.modalEnabled.checked;
    const editing = Boolean(state.editingUser);
    const payload = editing ? { enabled } : { username, password, enabled };

    if (editing) {
      if (password) {
        payload.password = password;
      }
    }

    if (!editing && !password) {
      elements.userFormError.textContent = "Введите пароль для нового пользователя.";
      return;
    }

    elements.saveUserButton.disabled = true;
    elements.saveUserButton.textContent = editing ? "Сохраняем..." : "Создаём...";

    try {
      if (editing) {
        await api(`/proxy-users/${encodeURIComponent(state.editingUser.username)}`, {
          method: "PATCH",
          body: payload,
        });
      } else {
        await api("/proxy-users", {
          method: "POST",
          body: payload,
        });
      }
      closeUserModal();
      await loadUsers();
    } catch (error) {
      elements.userFormError.textContent = error.message;
    } finally {
      elements.saveUserButton.disabled = false;
      elements.saveUserButton.textContent = editing ? "Сохранить" : "Создать";
    }
  }

  async function handleDeleteUser() {
    if (!state.deletingUser) {
      return;
    }

    elements.deleteError.textContent = "";
    elements.confirmDeleteButton.disabled = true;
    elements.confirmDeleteButton.textContent = "Удаляем...";

    try {
      await api(`/proxy-users/${encodeURIComponent(state.deletingUser.username)}`, {
        method: "DELETE",
      });
      closeDeleteModal();
      await loadUsers();
    } catch (error) {
      elements.deleteError.textContent = error.message;
    } finally {
      elements.confirmDeleteButton.disabled = false;
      elements.confirmDeleteButton.textContent = "Удалить";
    }
  }

  async function bootstrap() {
    const hasSession = restoreSession();
    if (!hasSession) {
      showLogin();
      return;
    }

    showDashboard();
    try {
      await loadUsers();
    } catch (error) {
      elements.loginError.textContent = error.message;
      clearSession();
      showLogin();
    }
  }

  elements.loginForm.addEventListener("submit", handleLogin);
  elements.logoutButton.addEventListener("click", () => {
    clearSession();
    showLogin();
  });
  elements.createUserButton.addEventListener("click", openCreateModal);
  elements.refreshButton.addEventListener("click", () => loadUsers().catch((error) => alert(error.message)));
  elements.userForm.addEventListener("submit", handleSaveUser);
  elements.closeUserModal.addEventListener("click", closeUserModal);
  elements.cancelUserModal.addEventListener("click", closeUserModal);
  elements.closeDeleteModal.addEventListener("click", closeDeleteModal);
  elements.cancelDeleteModal.addEventListener("click", closeDeleteModal);
  elements.confirmDeleteButton.addEventListener("click", handleDeleteUser);

  [elements.userModal, elements.deleteModal].forEach((modal) => {
    modal.addEventListener("click", (event) => {
      if (event.target === modal) {
        modal.classList.add("hidden");
      }
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeUserModal();
      closeDeleteModal();
    }
  });

  bootstrap();
})();
