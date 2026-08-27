from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
URL = "http://127.0.0.1:4173"
OUTPUT_DIR = ROOT / "work"
OUTPUT_DIR.mkdir(exist_ok=True)


def assert_loaded_images(page, selector, expected_count):
    images = page.locator(selector)
    assert images.count() == expected_count, (
        f"Expected {expected_count} images for {selector}, got {images.count()}"
    )
    failures = images.evaluate_all(
        "els => els.filter(el => !el.complete || el.naturalWidth === 0).map(el => el.src)"
    )
    assert not failures, f"Images failed to load: {failures}"


with sync_playwright() as playwright:
    launch_options = {"headless": True}
    if Path(CHROME).is_file():
        launch_options["executable_path"] = CHROME
    browser = playwright.chromium.launch(**launch_options)
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    console_errors = []
    page_errors = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page_errors.append(str(error)))

    page.goto(URL, wait_until="networkidle")

    assert_loaded_images(page, ".hero-portrait [data-portrait]", 1)
    portrait = page.locator(".hero-portrait [data-portrait]")
    assert portrait.get_attribute("src").endswith("assets/images/shanun-randev-portrait.png")
    natural_size = portrait.evaluate("image => [image.naturalWidth, image.naturalHeight]")
    assert natural_size == [1122, 1402]
    frame_box = page.locator(".hero-portrait-frame").bounding_box()
    frame_ratio = frame_box["width"] / frame_box["height"]
    assert 0.79 <= frame_ratio <= 0.81, f"Unexpected portrait frame ratio: {frame_ratio}"
    page.locator("#hero").screenshot(path=str(OUTPUT_DIR / "hero-desktop.png"))

    page.locator("#projects").scroll_into_view_if_needed()
    page.wait_for_timeout(400)

    assert page.locator(".project-card").count() == 21
    assert_loaded_images(page, ".project-card .pc-img", 21)

    page.locator("#experience").scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    assert_loaded_images(page, "#experience-timeline .logo-chip img", 5)

    page.locator("#education").scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    assert_loaded_images(page, "#education-grid .logo-chip img", 2)
    assert page.locator(".logo-chip--failed").count() == 0

    first_logo = page.locator("#experience-timeline .logo-chip img").first
    first_logo.evaluate("image => image.dispatchEvent(new Event('error'))")
    assert page.locator("#experience-timeline .logo-chip--failed").count() == 1
    assert page.locator("#experience-timeline .logo-chip-fallback").first.is_visible()

    page.reload(wait_until="networkidle")
    page.locator("#projects").scroll_into_view_if_needed()
    page.wait_for_timeout(300)

    first_card = page.locator(".project-card").first
    first_card.click()
    assert first_card.get_attribute("aria-expanded") == "true"

    media_box = first_card.locator(".pc-media").bounding_box()
    ratio = media_box["width"] / media_box["height"]
    assert 1.76 <= ratio <= 1.79, f"Unexpected project image ratio: {ratio}"

    page.screenshot(path=str(OUTPUT_DIR / "portfolio-desktop.png"), full_page=True)

    page.set_viewport_size({"width": 390, "height": 844})
    page.reload(wait_until="networkidle")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert_loaded_images(page, ".hero-portrait [data-portrait]", 1)
    page.locator("#hero").screenshot(path=str(OUTPUT_DIR / "hero-mobile.png"))
    assert_loaded_images(page, ".project-card .pc-img", 21)
    page.locator("#projects").scroll_into_view_if_needed()
    page.screenshot(path=str(OUTPUT_DIR / "projects-mobile-viewport.png"))
    page.screenshot(path=str(OUTPUT_DIR / "portfolio-mobile.png"), full_page=True)

    assert not page_errors, f"Page errors: {page_errors}"
    assert not console_errors, f"Console errors: {console_errors}"
    browser.close()

print("Browser verification passed: hero portrait, 21 project images, 7 logos, responsive layout, no console errors")
