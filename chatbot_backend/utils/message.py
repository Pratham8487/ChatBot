ERROR_MESSAGES = {
    # N8N
    "N8N_BASE_URL_MISSING": "N8N base URL is not set in Django settings.",

    # Repository
    "REPOSITORY_ID_MISSING": "Missing repository ID in the input payload.",
    "REPOSITORY_MISSING": "Repository not found for ID: {id}.",
    "REPO_ID_MISSING": "Missing both 'repository_id' and 'repo_name' in the input.",
    "REPO_NAME_NOT_FOUND": "Repository with name '{name}' not found.",
    "REPO_ID_NOT_FOUND": "Repository with ID '{id}' not found.",
    "MISSING_HOST_REPO_ID": "Host repository ID is missing.",
    "INVALID_REPO_PLATFORM": "Unsupported or unrecognized repository platform.",
    "INVALID_AZURE_URL": "Provided Azure DevOps repository URL is invalid.",
    "COMMIT_FETCH_FAILED": "Failed to fetch commits. Received status code: {status}.",

    # GitHub / Payload
    "INVALID_GITHUB_URL": "Invalid GitHub URL provided.",
    "INVALID_JSON": "The request body is not a valid JSON.",
    "ONLY_POST_ALLOWED": "Only POST requests are allowed.",
    "NO_COMMITS_AVAILABLE": "No commits found for the specified parameters.",
    "MISSING_DATA": "One or more required fields are missing.",

    # LLM
    "MISSING_PROMPT": "Prompt is missing from the request.",
    "INVALID_LLM_RESPONSE": "Received an invalid or unparsable response from the LLM.",
    "LLM_INTERNAL_ERROR": "An internal server error occurred while generating the summary.",
    "PROMPT_NOT_FOUND": "Prompt file not found for the given user level.",
    "INVALID_ENGINE": "Specified engine is not supported.",
    "LMSTUDIO_FAILURE": "LM Studio request failed.",

    # Email
    "EMAIL_TEMPLATE_MISSING": "Email template not found for the stakeholder and summary type combination.",
    "CONTACT_CONFIGURATION_ERROR": "Sender contact is not configured correctly.",
    "MISSING_DATA_FOR_CONTACT_CREATION": "Missing one or more required fields: contact_name, contact_email, stakeholder_id, project_id.",
    "NO_RECIPIENTS_FOUND": "No active contacts found for stakeholder '{stakeholder}' in project '{project}'.",
    "NO_RECIPIENTS": "No recipients given.",

    # Stakeholder / Project
    "STAKEHOLDER_MISSING": "Stakeholder not found or inactive for ID: {id}.",
    "MISSING_STAKEHOLDER_ID": "Stakeholder ID is required.",
    "MISSING_PULL_REQUEST_ID": "Pull request ID is missing in the request body.",

    # General
    "SERVER_ERROR": "An unexpected error occurred on the server.",
    "UNKNOWN_LANGUAGE": "The programming language is unknown or unsupported.",
    "FORMAT_FAILED": "Failed to format data.",
    "MISSING_SHA_OR_STAKEHOLDER": "Missing commit SHA or stakeholder_id.",
    "UNSUPPORTED_EVENT_TYPE": "Event type {event_type} not supported",
    "FAILED_FORMAT": "Failed to format Azure DevOps webhook payload",
    
    # User 
    "AUTHENTICATION_INVALID":"Authentication credentials were not provided or invalid.",
    'MISSING_CREDENTIALS': 'Email and password are required.',
    'INVALID_EMAIL': 'Invalid email format.',
    'EMAIL_EXISTS': 'User with this email already exists.',
    'CONTACT_EXISTS': 'User with this contact number already exists.',
    'INVALID_CREDENTIALS': 'Invalid email or password.',
    'MISSING_CREDENTIALS': 'Email and password are required.',
    'SERVER_ERROR': 'An unexpected error occurred.',
    'USER_INVALID': 'User not found.',
    'NEW_PASSWORD_MISSING' : 'New password is required.',
    'INCORRECT_PASSWORD': 'Password provided is incorrect.',
    "MISSING_TENANT": "User has no assigned tenant.",
    
    # Project
    "PROJECT_NAME_AND_LINK_MISSING": "Project name and project link are required.",
    "INVALID_URL": "The provided project link is invalid or inaccessible.",
    "EXPIRED_ACCESS_TOKEN": "The access token has expired.",
    "PROJECT_ALREADY_EXISTS": "A project with this link already exists.",
    "ACCESS_TOKEN_REQUIRED": "Access token is required for Azure DevOps repositories.",
    "PROJECT_NOT_FOUND": "Project not found or inactive.",
    
    # Repository
    "REPO_REQUIRED_FIELDS": "project_id, repository_name, and repository_link are required.",
    "PROJECT_NOT_FOUND_OR_UNAUTHORIZED": "The project does not exist or does not belong to the user.",
    "REPOSITORY_ALREADY_EXISTS": "A repository with this name already exists in the project.",
    
    
    # Email Verification 
    "USER_NOT_FOUND": "User not found with the provided credentials.",
    "EMAIL_NOT_PROVIDED": "Email address is missing in the request.",
    "INVALID_VERIFICATION_FIELD": "Invalid verification field. Supported values are 'email' and 'contact_number'.",
    "OTP_GENERATION_FAILED": "Failed to generate OTP. Please try again.",
    "OTP_EXPIRED": "The OTP has expired. Please request a new one.",
    "OTP_INVALID": "The OTP entered is incorrect.",
    "OTP_ATTEMPTS_EXCEEDED": "Maximum OTP verification attempts exceeded. Please request a new OTP.",
    "OTP_ALREADY_VERIFIED": "The OTP has already been verified.",
    "MISSING_OTP": "OTP is missing in the request.",
    "MISSING_VERIFICATION_DATA": "Required verification data is missing.",

    # Tenant
    "TENANT_CREATE_PERMISSION_DENIED": "Permission denied. Only Super Admin can create tenants.",
    "TENANT_UPDATE_PERMISSION_DENIED": "Permission denied. Only the creator can update this tenant.",
    "TENANT_DELETE_PERMISSION_DENIED": "Permission denied. Only the creator can delete this tenant.",
    "TENANT_CREATE_FAILED": "Error creating tenant",
    "TENANT_DETAIL_FAILED": "Error fetching tenant details",
    "TENANT_UPDATE_FAILED": "Error updating tenant",
    "TENANT_DELETE_FAILED": "Error deleting tenant",
    "TENANT_LIST_FAILED": "Error fetching tenant list",
    "TENANT_NOT_FOUND": "Tenant not found or already inactive.",
    
    # Group
    "MISSING_GROUP_NAME": "Group name is required.",
    
    # Objective
    "MISSING_OBJECTIVE_NAME": "Objective name is required.",
    
    # Assessment
    "MISSING_ASSESSMENT_NAME": "Assessment name is required and cannot be empty. ",
    
    "INVALID_RECEIVING_UPDATES": "Receiving Updates is required and must be one of: daily, weekly, monthly, quarterly.",

    # Roles
    "ADMIN_ROLE_DENIED": "Only Admin users can create roles.",
    "ROLE_CREATE_FAILED": "Failed to create role. Please try again.",
    "ROLE_CREATE_PERMISSION_DENIED": "You do not have permission to create roles.",
    
    "ROLE_DELETE_PERMISSION_DENIED": "Only Admin users can delete roles.",
    "ROLE_DELETE_FAILED": "Failed to delete role. Please try again.",
    "ROLE_NOT_FOUND": "Role not found or already inactive.",
    "ROLE_ID_REQUIRED": "Role ID is required.",
    "ROLE_ALREADY_INACTIVE": "Role is already inactive.",
    "ROLE_IN_USE": "Cannot delete role as it is currently assigned to users.",
    "ROLE_EDIT_PERMISSION_DENIED": "Only Admin users can edit roles.",
    "ROLE_EDIT_FAILED": "Failed to update role. Please try again.",
    
    # Group 
    "GROUP_CREATE_FAILED": "Failed to create group",
    "GROUP_UPDATE_FAILED": "Failed to update group",
    "GROUP_DELETE_FAILED": "Failed to delete group",
    "GROUP_LIST_FAILED": "Failed to fetch groups",
    "GROUP_DETAIL_FAILED": "Failed to fetch group details",
    "GROUP_PERMISSION_DENIED": "You don't have permission to access this group",
    
    # objective
    "OBJECTIVE_CREATE_FAILED": "Failed to create objective",
    "OBJECTIVE_UPDATE_FAILED": "Failed to update objective",
    "OBJECTIVE_DELETE_FAILED": "Failed to delete objective",
    "OBJECTIVE_LIST_FAILED": "Failed to fetch objectives",
    "OBJECTIVE_DETAIL_FAILED": "Failed to fetch objective details",
    "OBJECTIVE_PERMISSION_DENIED": "You don't have permission to access this objective",
    "OBJECTIVE_CREATED": "Objective created successfully",
    
    # Assessment
    "ASSESSMENT_CREATED": "Assessment created successfully.",
    "ASSESSMENT_CREATION_FAILED": "Failed to create assessment.",
    "ASSESSMENT_UPDATED": "Assessment updated successfully.",
    "ASSESSMENT_UPDATE_FAILED": "Failed to update assessment.",
    
    # Assessment Response
    "INVALID_TENANT": "No tenant found for the user.",
    "INVALID_ASSESSMENT": "Assessment not found or inactive.",
    "EMPTY_RESPONSE": "Response data cannot be empty.",
    "MAX_RESPONSE_EXCEEDED": "Response is too long (maximum 10000 characters).",
    "MISSING_PATH": "File path not specified",
    "INVALID_PATH": "Invalid file path",
    "FILE_NOT_FOUND": "File not found",
    "UNAUTHORIZED": "Unauthorized access",

}

SUCCESS_MESSAGES = {
    "SUMMARY_GENERATED": "LLM summary generated successfully.",
    "SUMMARY_SUCCESS": "Summary generated successfully.",
    "EMAIL_SENT": "Email sent successfully.",
    "N8N_TRIGGERED": "N8N workflow triggered successfully.",
    "PR_REVIEW_SUCCESS": "Pull request review email sent successfully.",
    "OTP_SENT": "OTP has been sent successfully to the user's email.",
    "OTP_VERIFIED": "OTP has been successfully verified.",
    "EMAIL_ALREADY_VERIFIED" : "Email is already verified.",
    "PASSWORD_UPDATED": "Password updated successfully.",
    
    # Tenant
    "TENANT_CREATED": "Tenant created successfully.",
    "TENANT_UPDATED": "Tenant updated successfully.",
    "TENANT_DELETED": "Tenant deleted successfully.",
    
    # Role
    "ROLE_CREATED": "Role created successfully.",
    "ROLE_DELETED": "Role deleted successfully.",
    "ROLE_UPDATED": "Role updated successfully.",
    
    # Group
    "GROUP_CREATED": "Group created successfully.",
    "GROUP_UPDATED": "Group updated successfully.",
    "GROUP_DELETED": "Group deleted successfully.",
    "GROUP_ACTIVATED": "Group activated successfully.",
    "GROUP_DEACTIVATED": "Group deactivated successfully.",

    # Objective
    "OBJECTIVE_CREATED": "Objective created successfully.",
    "OBJECTIVE_UPDATED": "Objective updated successfully.",
    
    # Assessment
    "ASSESSMENT_CREATED": "Assessment created successfully.",
    "ASSESSMENT_UPDATED": "Assessment updated successfully.",

}

INFO_MESSAGES = {
    # General
    "FINAL_PROMPT_CONSTRUCTED": "Final prompt constructed with {length} characters.",

    # GitHub / Commits
    "COMMITS_SUMMARIZED": "{count} commit(s) summarized.",

    # Email
    "EMAIL_SENT": "Email sent successfully. Log ID: {log_id}.",

    # N8N
    "N8N_SENT": "Summary sent to N8N. Response status: {status}.",

    # Prompt
    "LOOKING_FOR_PROMPT": "Searching for prompt at path: {path}.",
    "PROMPT_LOADED": "Prompt loaded with {length} characters.",

    # LLM Engines
    "OLLAMA_GENERATING": "Generating summary using Ollama...",
    "OLLAMA_COMPLETE": "Ollama summary generated in {duration}s.",
    "OLLAMA_LOCAL_SERVER": "Using local Ollama server.",
    "OLLAMA_REMOTE_SERVER": "Using remote Ollama server at IP: {ip}.",

    "OPENAI_GENERATING": "Generating summary using OpenAI...",
    "OPENAI_KEY_LOADED": "OpenAI API key loaded successfully.",
    "OPENAI_COMPLETE": "OpenAI summary generated in {duration}s.",

    "LMSTUDIO_GENERATING": "Generating summary using LM Studio...",
    "LMSTUDIO_COMPLETE": "LM Studio summary generated in {duration}s.",
    "CUSTOM_EMAIL_SENT": "Custom email is send.",
    
    # Email verification
    "OTP_DISPATCH_INITIATED": "Starting OTP dispatch process for user: {email}.",
    "OTP_DISPATCH_SUCCESS": "OTP email sent to: {email}.",
    "OTP_VERIFICATION_ATTEMPT": "Attempting OTP verification for user: {email}.",
    "OTP_EXPIRED_CHECK": "Checking if OTP is expired for user: {email}.",
    "OTP_ATTEMPT_LIMIT_REACHED": "User {email} exceeded max OTP attempts.",


}

STATUS_MESSAGES = {
    "HEALTHY": "Healthy",
    "UNHEALTHY": "Unhealthy",
    "UNKNOWN": "Unknown",
}
