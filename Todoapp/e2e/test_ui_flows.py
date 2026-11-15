"""
Browser tests for the main user journeys.

Run:   python -m pytest Todoapp/e2e -v
Watch: python -m pytest Todoapp/e2e --headed --slowmo 500
"""
import re

from playwright.sync_api import Page, expect


def test_unauthenticated_user_is_redirected_to_login(page: Page):
    page.goto("/todos")
    expect(page).to_have_url(re.compile(r".*/login$"))
    expect(page.get_by_role("heading", name="Login")).to_be_visible()


def test_login_with_wrong_password_shows_error(page: Page, register, new_user):
    register(new_user)
    page.locator("input[type=text]").fill(new_user["username"])
    page.locator("input[type=password]").fill("wrong-password")
    page.get_by_role("button", name="Login").click()
    expect(page.locator(".alert-danger")).to_have_text("Invalid username or password")


def test_register_login_and_add_todo(page: Page, register, login, new_user):
    register(new_user)
    login(new_user)
    expect(page.get_by_text("You have no todos yet.")).to_be_visible()

    page.get_by_role("link", name="Add New Todo").click()
    page.get_by_placeholder("Enter title").fill("Write Playwright tests")
    page.get_by_placeholder("Enter description").fill("Cover the main UI flows")
    page.locator("form select").select_option("4")
    page.get_by_role("button", name="Add Todo").click()

    expect(page).to_have_url(re.compile(r".*/todos$"))
    expect(page.get_by_role("cell", name="Write Playwright tests")).to_be_visible()


def test_regular_user_does_not_see_admin_link(page: Page, register, login, new_user):
    register(new_user, role="user")
    login(new_user)
    expect(page.get_by_role("link", name="Users")).to_have_count(0)


def test_admin_sees_users_link(page: Page, register, login, new_user):
    register(new_user, role="admin")
    login(new_user)
    page.get_by_role("link", name="Users").click()
    expect(page).to_have_url(re.compile(r".*/admin/users$"))


def test_logout_returns_to_login(page: Page, register, login, new_user):
    register(new_user)
    login(new_user)
    page.get_by_role("button", name="Logout").click()
    expect(page).to_have_url(re.compile(r".*/login$"))
    expect(page.get_by_role("navigation").get_by_role("link", name="Register")).to_be_visible()
