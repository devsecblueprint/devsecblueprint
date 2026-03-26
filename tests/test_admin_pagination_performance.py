"""
Pagination performance tests for admin submissions endpoint.

Tests pagination behavior with large datasets, page_size enforcement,
cursor-based pagination, and performance characteristics.

Validates Requirements 1.7, 11.7
"""

import pytest
import time
from unittest.mock import Mock, patch
from backend.handlers.admin_submissions import handle_get_submissions


class TestPaginationPerformance:
    """Test pagination performance and correctness for submissions endpoint."""

    @patch("backend.handlers.admin_submissions.boto3")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_large_dataset_pagination(self, mock_boto3):
        """
        Test pagination with large submission datasets.

        Validates: Requirements 1.7, 11.7
        **Validates: Requirements 1.7, 11.7**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock DynamoDB response with 500 submissions
        mock_dynamodb = Mock()
        mock_boto3.client.return_value = mock_dynamodb

        # Create 500 mock submissions
        mock_items = []
        for i in range(500):
            mock_items.append(
                {
                    "PK": {"S": f"USER#github|{12345 + i}"},
                    "SK": {"S": f"CAPSTONE_SUBMISSION#capstone-{i}"},
                    "github_username": {"S": f"learner{i}"},
                    "repo_url": {"S": f"https://github.com/learner{i}/capstone"},
                    "submitted_at": {
                        "S": f"2024-01-{1 + (i % 28):02d}T{(i % 24):02d}:30:00Z"
                    },
                    "updated_at": {
                        "S": f"2024-01-{1 + (i % 28):02d}T{(i % 24):02d}:30:00Z"
                    },
                }
            )

        mock_dynamodb.scan.return_value = {"Items": mock_items, "Count": 500}

        # Test: Request first page with default page size (50)
        start_time = time.time()
        response = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"},
            query_params={"page": "1", "page_size": "50"},
        )
        elapsed_time = time.time() - start_time

        # Verify: Response is successful
        assert response["statusCode"] == 200

        # Parse response
        import json

        body = json.loads(response["body"])

        # Verify: Returns correct page size
        assert len(body["submissions"]) == 50
        assert body["page"] == 1
        assert body["page_size"] == 50
        assert body["total_count"] == 500
        assert body["total_pages"] == 10

        # Verify: Performance is acceptable for large dataset
        assert elapsed_time < 2.0, f"Large dataset pagination took {elapsed_time:.3f}s"

        print(f"✓ Large dataset (500 items) paginated in {elapsed_time:.3f}s")

    @patch("backend.handlers.admin_submissions.boto3")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_page_size_limit_enforced(self, mock_boto3):
        """
        Test that page_size parameter is enforced with maximum of 100.

        Validates: Requirements 1.7, 11.7
        **Validates: Requirements 1.7, 11.7**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock DynamoDB response with 200 submissions
        mock_dynamodb = Mock()
        mock_boto3.client.return_value = mock_dynamodb

        mock_items = []
        for i in range(200):
            mock_items.append(
                {
                    "PK": {"S": f"USER#github|{12345 + i}"},
                    "SK": {"S": f"CAPSTONE_SUBMISSION#capstone-{i}"},
                    "github_username": {"S": f"learner{i}"},
                    "repo_url": {"S": f"https://github.com/learner{i}/capstone"},
                    "submitted_at": {"S": f"2024-01-15T10:{i % 60:02d}:00Z"},
                    "updated_at": {"S": f"2024-01-15T10:{i % 60:02d}:00Z"},
                }
            )

        mock_dynamodb.scan.return_value = {"Items": mock_items, "Count": 200}

        # Test: Request with page_size exceeding maximum (150 > 100)
        response = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"},
            query_params={"page": "1", "page_size": "150"},
        )

        # Verify: Request is rejected with 400 Bad Request
        assert response["statusCode"] == 400

        import json

        body = json.loads(response["body"])
        assert "Page size must be between 1 and 100" in body["error"]

        print("✓ Page size limit (max 100) enforced correctly")

    @patch("backend.handlers.admin_submissions.boto3")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_page_size_minimum_enforced(self, mock_boto3):
        """
        Test that page_size parameter enforces minimum of 1.

        Validates: Requirements 1.7
        **Validates: Requirements 1.7**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock DynamoDB
        mock_dynamodb = Mock()
        mock_boto3.client.return_value = mock_dynamodb

        # Test: Request with page_size below minimum (0 < 1)
        response = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"},
            query_params={"page": "1", "page_size": "0"},
        )

        # Verify: Request is rejected with 400 Bad Request
        assert response["statusCode"] == 400

        import json

        body = json.loads(response["body"])
        assert "Page size must be between 1 and 100" in body["error"]

        print("✓ Page size minimum (1) enforced correctly")

    @patch("backend.handlers.admin_submissions.boto3")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_page_size_exactly_100_allowed(self, mock_boto3):
        """
        Test that page_size of exactly 100 is allowed.

        Validates: Requirements 1.7, 11.7
        **Validates: Requirements 1.7, 11.7**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock DynamoDB response with 150 submissions
        mock_dynamodb = Mock()
        mock_boto3.client.return_value = mock_dynamodb

        mock_items = []
        for i in range(150):
            mock_items.append(
                {
                    "PK": {"S": f"USER#github|{12345 + i}"},
                    "SK": {"S": f"CAPSTONE_SUBMISSION#capstone-{i}"},
                    "github_username": {"S": f"learner{i}"},
                    "repo_url": {"S": f"https://github.com/learner{i}/capstone"},
                    "submitted_at": {"S": f"2024-01-15T10:30:{i % 60:02d}Z"},
                    "updated_at": {"S": f"2024-01-15T10:30:{i % 60:02d}Z"},
                }
            )

        mock_dynamodb.scan.return_value = {"Items": mock_items, "Count": 150}

        # Test: Request with page_size exactly 100
        response = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"},
            query_params={"page": "1", "page_size": "100"},
        )

        # Verify: Request is successful
        assert response["statusCode"] == 200

        import json

        body = json.loads(response["body"])

        # Verify: Returns exactly 100 items
        assert len(body["submissions"]) == 100
        assert body["page_size"] == 100
        assert body["total_count"] == 150
        assert body["total_pages"] == 2

        print("✓ Page size of exactly 100 allowed")

    @patch("backend.handlers.admin_submissions.boto3")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_pagination_across_multiple_pages(self, mock_boto3):
        """
        Test pagination correctness across multiple pages.

        Validates: Requirements 1.7, 11.7
        **Validates: Requirements 1.7, 11.7**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock DynamoDB response with 125 submissions
        mock_dynamodb = Mock()
        mock_boto3.client.return_value = mock_dynamodb

        mock_items = []
        for i in range(125):
            mock_items.append(
                {
                    "PK": {"S": f"USER#github|{12345 + i}"},
                    "SK": {"S": f"CAPSTONE_SUBMISSION#capstone-{i:03d}"},
                    "github_username": {"S": f"learner{i:03d}"},
                    "repo_url": {"S": f"https://github.com/learner{i:03d}/capstone"},
                    "submitted_at": {
                        "S": f"2024-01-15T{10 + (i // 60):02d}:{i % 60:02d}:00Z"
                    },
                    "updated_at": {
                        "S": f"2024-01-15T{10 + (i // 60):02d}:{i % 60:02d}:00Z"
                    },
                }
            )

        mock_dynamodb.scan.return_value = {"Items": mock_items, "Count": 125}

        # Test: Request page 1 (50 items)
        response1 = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"},
            query_params={"page": "1", "page_size": "50"},
        )

        # Test: Request page 2 (50 items)
        response2 = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"},
            query_params={"page": "2", "page_size": "50"},
        )

        # Test: Request page 3 (25 items)
        response3 = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"},
            query_params={"page": "3", "page_size": "50"},
        )

        # Verify: All responses are successful
        assert response1["statusCode"] == 200
        assert response2["statusCode"] == 200
        assert response3["statusCode"] == 200

        import json

        body1 = json.loads(response1["body"])
        body2 = json.loads(response2["body"])
        body3 = json.loads(response3["body"])

        # Verify: Page 1 has 50 items
        assert len(body1["submissions"]) == 50
        assert body1["page"] == 1
        assert body1["total_pages"] == 3

        # Verify: Page 2 has 50 items
        assert len(body2["submissions"]) == 50
        assert body2["page"] == 2
        assert body2["total_pages"] == 3

        # Verify: Page 3 has 25 items (remainder)
        assert len(body3["submissions"]) == 25
        assert body3["page"] == 3
        assert body3["total_pages"] == 3

        # Verify: All pages have same total_count
        assert body1["total_count"] == 125
        assert body2["total_count"] == 125
        assert body3["total_count"] == 125

        # Verify: No duplicate submissions across pages
        usernames_page1 = {s["github_username"] for s in body1["submissions"]}
        usernames_page2 = {s["github_username"] for s in body2["submissions"]}
        usernames_page3 = {s["github_username"] for s in body3["submissions"]}

        assert (
            len(usernames_page1 & usernames_page2) == 0
        ), "Pages 1 and 2 have duplicates"
        assert (
            len(usernames_page1 & usernames_page3) == 0
        ), "Pages 1 and 3 have duplicates"
        assert (
            len(usernames_page2 & usernames_page3) == 0
        ), "Pages 2 and 3 have duplicates"

        print("✓ Pagination across multiple pages works correctly")

    @patch("backend.handlers.admin_submissions.boto3")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_pagination_performance_does_not_degrade(self, mock_boto3):
        """
        Test that pagination performance doesn't degrade with page number.

        Validates: Requirements 11.7
        **Validates: Requirements 11.7**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock DynamoDB response with 500 submissions
        mock_dynamodb = Mock()
        mock_boto3.client.return_value = mock_dynamodb

        mock_items = []
        for i in range(500):
            mock_items.append(
                {
                    "PK": {"S": f"USER#github|{12345 + i}"},
                    "SK": {"S": f"CAPSTONE_SUBMISSION#capstone-{i}"},
                    "github_username": {"S": f"learner{i}"},
                    "repo_url": {"S": f"https://github.com/learner{i}/capstone"},
                    "submitted_at": {
                        "S": f"2024-01-{1 + (i % 28):02d}T{(i % 24):02d}:30:00Z"
                    },
                    "updated_at": {
                        "S": f"2024-01-{1 + (i % 28):02d}T{(i % 24):02d}:30:00Z"
                    },
                }
            )

        mock_dynamodb.scan.return_value = {"Items": mock_items, "Count": 500}

        # Test: Measure performance for page 1, 5, and 10
        pages_to_test = [1, 5, 10]
        timings = []

        for page_num in pages_to_test:
            start_time = time.time()
            response = handle_get_submissions(
                headers={"Cookie": f"dsb_token={token}"},
                query_params={"page": str(page_num), "page_size": "50"},
            )
            elapsed_time = time.time() - start_time

            # Verify: Response is successful
            assert response["statusCode"] == 200

            # Verify: Response time is under 2 seconds
            assert elapsed_time < 2.0, f"Page {page_num} took {elapsed_time:.3f}s"

            timings.append((page_num, elapsed_time))
            print(f"  Page {page_num}: {elapsed_time:.3f}s")

        # Verify: Performance doesn't significantly degrade
        # Last page should not be more than 2x slower than first page
        first_page_time = timings[0][1]
        last_page_time = timings[-1][1]

        assert last_page_time < first_page_time * 2, (
            f"Performance degraded: page 1 took {first_page_time:.3f}s, "
            f"page 10 took {last_page_time:.3f}s"
        )

        print(f"✓ Pagination performance consistent across pages")

    @patch("backend.handlers.admin_submissions.boto3")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_cursor_based_pagination_with_last_evaluated_key(self, mock_boto3):
        """
        Test cursor-based pagination using DynamoDB LastEvaluatedKey.

        This test verifies that the implementation correctly handles
        DynamoDB's pagination mechanism using LastEvaluatedKey.

        Validates: Requirements 1.7, 11.7
        **Validates: Requirements 1.7, 11.7**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock DynamoDB to return data in chunks with LastEvaluatedKey
        mock_dynamodb = Mock()
        mock_boto3.client.return_value = mock_dynamodb

        # Create 300 submissions split across 3 DynamoDB scan calls
        all_items = []
        for i in range(300):
            all_items.append(
                {
                    "PK": {"S": f"USER#github|{12345 + i}"},
                    "SK": {"S": f"CAPSTONE_SUBMISSION#capstone-{i}"},
                    "github_username": {"S": f"learner{i}"},
                    "repo_url": {"S": f"https://github.com/learner{i}/capstone"},
                    "submitted_at": {
                        "S": f"2024-01-{1 + (i % 28):02d}T{(i % 24):02d}:30:00Z"
                    },
                    "updated_at": {
                        "S": f"2024-01-{1 + (i % 28):02d}T{(i % 24):02d}:30:00Z"
                    },
                }
            )

        # Mock DynamoDB to return data in 3 chunks (simulating LastEvaluatedKey)
        scan_call_count = [0]

        def mock_scan(**kwargs):
            call_num = scan_call_count[0]
            scan_call_count[0] += 1

            if call_num == 0:
                # First call: return items 0-99 with LastEvaluatedKey
                return {
                    "Items": all_items[0:100],
                    "Count": 100,
                    "LastEvaluatedKey": {
                        "PK": {"S": "USER#github|12444"},
                        "SK": {"S": "CAPSTONE_SUBMISSION#capstone-99"},
                    },
                }
            elif call_num == 1:
                # Second call: return items 100-199 with LastEvaluatedKey
                return {
                    "Items": all_items[100:200],
                    "Count": 100,
                    "LastEvaluatedKey": {
                        "PK": {"S": "USER#github|12544"},
                        "SK": {"S": "CAPSTONE_SUBMISSION#capstone-199"},
                    },
                }
            else:
                # Third call: return items 200-299 without LastEvaluatedKey
                return {"Items": all_items[200:300], "Count": 100}

        mock_dynamodb.scan.side_effect = mock_scan

        # Test: Request first page
        start_time = time.time()
        response = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"},
            query_params={"page": "1", "page_size": "50"},
        )
        elapsed_time = time.time() - start_time

        # Verify: Response is successful
        assert response["statusCode"] == 200

        import json

        body = json.loads(response["body"])

        # Verify: Returns correct data
        assert len(body["submissions"]) == 50
        assert body["total_count"] == 300
        assert body["page"] == 1
        assert body["page_size"] == 50
        assert body["total_pages"] == 6

        # Verify: DynamoDB scan was called multiple times (cursor-based pagination)
        assert (
            mock_dynamodb.scan.call_count == 3
        ), f"Expected 3 scan calls for cursor-based pagination, got {mock_dynamodb.scan.call_count}"

        # Verify: Performance is acceptable even with multiple scan calls
        assert elapsed_time < 2.0, f"Cursor-based pagination took {elapsed_time:.3f}s"

        print(f"✓ Cursor-based pagination with LastEvaluatedKey works correctly")
        print(
            f"  Processed 300 items across 3 DynamoDB scan calls in {elapsed_time:.3f}s"
        )

    @patch("backend.handlers.admin_submissions.boto3")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_empty_dataset_pagination(self, mock_boto3):
        """
        Test pagination behavior with empty dataset.

        Validates: Requirements 1.7
        **Validates: Requirements 1.7**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock DynamoDB response with no submissions
        mock_dynamodb = Mock()
        mock_boto3.client.return_value = mock_dynamodb

        mock_dynamodb.scan.return_value = {"Items": [], "Count": 0}

        # Test: Request page 1
        response = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"},
            query_params={"page": "1", "page_size": "50"},
        )

        # Verify: Response is successful
        assert response["statusCode"] == 200

        import json

        body = json.loads(response["body"])

        # Verify: Returns empty list
        assert len(body["submissions"]) == 0
        assert body["total_count"] == 0
        assert body["page"] == 1
        assert body["page_size"] == 50
        assert body["total_pages"] == 0

        print("✓ Empty dataset pagination handled correctly")

    @patch("backend.handlers.admin_submissions.boto3")
    @patch.dict(
        "os.environ",
        {"PROGRESS_TABLE": "test-progress-table", "JWT_SECRET_NAME": "test-jwt-secret"},
    )
    def test_single_item_pagination(self, mock_boto3):
        """
        Test pagination with single item dataset.

        Validates: Requirements 1.7
        **Validates: Requirements 1.7**
        """
        from backend.auth.jwt_utils import generate_jwt

        # Generate admin JWT token
        token = generate_jwt(
            user_id="github|12345",
            username="damienjburks",
            github_username="damienjburks",
        )

        # Setup: Mock DynamoDB response with 1 submission
        mock_dynamodb = Mock()
        mock_boto3.client.return_value = mock_dynamodb

        mock_dynamodb.scan.return_value = {
            "Items": [
                {
                    "PK": {"S": "USER#github|12345"},
                    "SK": {"S": "CAPSTONE_SUBMISSION#capstone-1"},
                    "github_username": {"S": "learner1"},
                    "repo_url": {"S": "https://github.com/learner1/capstone"},
                    "submitted_at": {"S": "2024-01-15T10:30:00Z"},
                    "updated_at": {"S": "2024-01-15T10:30:00Z"},
                }
            ],
            "Count": 1,
        }

        # Test: Request page 1
        response = handle_get_submissions(
            headers={"Cookie": f"dsb_token={token}"},
            query_params={"page": "1", "page_size": "50"},
        )

        # Verify: Response is successful
        assert response["statusCode"] == 200

        import json

        body = json.loads(response["body"])

        # Verify: Returns single item
        assert len(body["submissions"]) == 1
        assert body["total_count"] == 1
        assert body["page"] == 1
        assert body["page_size"] == 50
        assert body["total_pages"] == 1

        print("✓ Single item pagination handled correctly")
