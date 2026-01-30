#!/usr/bin/env python3
"""
Smoke test script for Aptly production deployment.

Verifies that the deployed application is working correctly by testing
the core API endpoints.

Usage:
    python scripts/smoke_test.py --url https://your-app.railway.app --admin-secret your-secret

    # With optional LLM test (requires real API key)
    python scripts/smoke_test.py --url https://your-app.railway.app --admin-secret your-secret \
        --openai-key sk-...
"""

import argparse
import asyncio
import sys
import uuid
from datetime import datetime

import httpx


class SmokeTestError(Exception):
    """Raised when a smoke test fails."""

    pass


class SmokeTest:
    def __init__(self, base_url: str, admin_secret: str, openai_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.admin_secret = admin_secret
        self.openai_key = openai_key
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_customer_id: str | None = None
        self.test_api_key: str | None = None

    async def close(self):
        await self.client.aclose()

    def _print_result(self, test_name: str, success: bool, detail: str = ""):
        status = "\033[92mPASS\033[0m" if success else "\033[91mFAIL\033[0m"
        print(f"  [{status}] {test_name}")
        if detail and not success:
            print(f"         {detail}")

    async def test_health_check(self) -> bool:
        """Test that health check returns healthy status."""
        try:
            response = await self.client.get(f"{self.base_url}/v1/health")
            data = response.json()

            if response.status_code != 200:
                self._print_result("Health check", False, f"Status: {response.status_code}")
                return False

            if data.get("status") != "healthy":
                self._print_result(
                    "Health check",
                    False,
                    f"Status: {data.get('status')}, Checks: {data.get('checks')}",
                )
                return False

            checks = data.get("checks", {})
            db_ok = checks.get("database") == "ok"
            redis_ok = checks.get("redis") == "ok"

            if not db_ok or not redis_ok:
                self._print_result(
                    "Health check",
                    False,
                    f"database: {checks.get('database')}, redis: {checks.get('redis')}",
                )
                return False

            self._print_result("Health check", True)
            return True

        except Exception as e:
            self._print_result("Health check", False, str(e))
            return False

    async def test_admin_create_customer(self) -> bool:
        """Test that admin can create a customer."""
        try:
            test_email = f"smoke-test-{uuid.uuid4().hex[:8]}@test.aptly.dev"

            response = await self.client.post(
                f"{self.base_url}/v1/admin/customers",
                headers={"X-Admin-Secret": self.admin_secret},
                json={
                    "email": test_email,
                    "company_name": "Smoke Test Co",
                    "plan": "free",
                },
            )

            if response.status_code != 201:
                self._print_result(
                    "Admin create customer",
                    False,
                    f"Status: {response.status_code}, Body: {response.text[:200]}",
                )
                return False

            data = response.json()
            self.test_customer_id = data["customer"]["id"]
            self.test_api_key = data["api_key"]["key"]

            self._print_result("Admin create customer", True)
            return True

        except Exception as e:
            self._print_result("Admin create customer", False, str(e))
            return False

    async def test_customer_authentication(self) -> bool:
        """Test that customer can authenticate with API key."""
        if not self.test_api_key:
            self._print_result("Customer authentication", False, "No API key from previous test")
            return False

        try:
            response = await self.client.get(
                f"{self.base_url}/v1/me",
                headers={"Authorization": f"Bearer {self.test_api_key}"},
            )

            if response.status_code != 200:
                self._print_result(
                    "Customer authentication",
                    False,
                    f"Status: {response.status_code}",
                )
                return False

            data = response.json()
            if data.get("id") != self.test_customer_id:
                self._print_result(
                    "Customer authentication",
                    False,
                    "Customer ID mismatch",
                )
                return False

            self._print_result("Customer authentication", True)
            return True

        except Exception as e:
            self._print_result("Customer authentication", False, str(e))
            return False

    async def test_list_api_keys(self) -> bool:
        """Test that customer can list their API keys."""
        if not self.test_api_key:
            self._print_result("List API keys", False, "No API key from previous test")
            return False

        try:
            response = await self.client.get(
                f"{self.base_url}/v1/api-keys",
                headers={"Authorization": f"Bearer {self.test_api_key}"},
            )

            if response.status_code != 200:
                self._print_result("List API keys", False, f"Status: {response.status_code}")
                return False

            data = response.json()
            if not data.get("api_keys"):
                self._print_result("List API keys", False, "No API keys returned")
                return False

            self._print_result("List API keys", True)
            return True

        except Exception as e:
            self._print_result("List API keys", False, str(e))
            return False

    async def test_query_audit_logs(self) -> bool:
        """Test that customer can query audit logs."""
        if not self.test_api_key:
            self._print_result("Query audit logs", False, "No API key from previous test")
            return False

        try:
            response = await self.client.get(
                f"{self.base_url}/v1/logs",
                headers={"Authorization": f"Bearer {self.test_api_key}"},
            )

            if response.status_code != 200:
                self._print_result("Query audit logs", False, f"Status: {response.status_code}")
                return False

            data = response.json()
            if "logs" not in data or "pagination" not in data:
                self._print_result("Query audit logs", False, "Invalid response structure")
                return False

            self._print_result("Query audit logs", True)
            return True

        except Exception as e:
            self._print_result("Query audit logs", False, str(e))
            return False

    async def test_chat_completion(self) -> bool:
        """Test chat completion endpoint (optional, requires OpenAI key)."""
        if not self.openai_key:
            self._print_result("Chat completion", True, "(skipped - no OpenAI key provided)")
            return True

        if not self.test_api_key:
            self._print_result("Chat completion", False, "No API key from previous test")
            return False

        try:
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.test_api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "Say 'smoke test passed' and nothing else."}],
                    "api_keys": {"openai": self.openai_key},
                    "max_tokens": 20,
                },
            )

            if response.status_code != 200:
                self._print_result(
                    "Chat completion",
                    False,
                    f"Status: {response.status_code}, Body: {response.text[:200]}",
                )
                return False

            data = response.json()
            if "choices" not in data or "aptly" not in data:
                self._print_result("Chat completion", False, "Invalid response structure")
                return False

            # Verify audit log was created
            if not data["aptly"].get("audit_log_id"):
                self._print_result("Chat completion", False, "No audit log ID in response")
                return False

            self._print_result("Chat completion", True)
            return True

        except Exception as e:
            self._print_result("Chat completion", False, str(e))
            return False

    async def run_all_tests(self) -> bool:
        """Run all smoke tests and return overall success."""
        print(f"\n{'='*60}")
        print(f"Aptly Smoke Test - {datetime.now().isoformat()}")
        print(f"Target: {self.base_url}")
        print(f"{'='*60}\n")

        results = []

        # Core tests
        results.append(await self.test_health_check())
        results.append(await self.test_admin_create_customer())
        results.append(await self.test_customer_authentication())
        results.append(await self.test_list_api_keys())
        results.append(await self.test_query_audit_logs())
        results.append(await self.test_chat_completion())

        # Summary
        passed = sum(results)
        total = len(results)
        success = all(results)

        print(f"\n{'='*60}")
        if success:
            print(f"\033[92mAll tests passed ({passed}/{total})\033[0m")
        else:
            print(f"\033[91mSome tests failed ({passed}/{total} passed)\033[0m")
        print(f"{'='*60}")

        # Cleanup note
        if self.test_customer_id:
            print(f"\nNote: Test customer created with ID: {self.test_customer_id}")
            print("      You may want to delete this customer manually.")

        return success


async def main():
    parser = argparse.ArgumentParser(description="Aptly Production Smoke Test")
    parser.add_argument(
        "--url",
        required=True,
        help="Base URL of the Aptly API (e.g., https://your-app.railway.app)",
    )
    parser.add_argument(
        "--admin-secret",
        required=True,
        help="Admin secret for creating test customer",
    )
    parser.add_argument(
        "--openai-key",
        help="OpenAI API key for testing chat completions (optional)",
    )

    args = parser.parse_args()

    smoke_test = SmokeTest(
        base_url=args.url,
        admin_secret=args.admin_secret,
        openai_key=args.openai_key,
    )

    try:
        success = await smoke_test.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        await smoke_test.close()


if __name__ == "__main__":
    asyncio.run(main())
