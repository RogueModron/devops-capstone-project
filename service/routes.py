"""
Account Service

This microservice handles the lifecycle of Accounts
"""
# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            # paths=url_for("list_accounts", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based the data in the body that is posted
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()
    location_url = url_for("read_accounts", account_id=account.id, _external=True)
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )

######################################################################
# LIST ALL ACCOUNTS
######################################################################

@app.route("/accounts")
def list_accounts():
    """
    List all Accounts
    This endpoint will return all the Accounts
    """
    accounts = Account.all()
    serialized_accounts = []
    for account in accounts:
        serialized_accounts.append(account.serialize())
    return jsonify(serialized_accounts), status.HTTP_200_OK

######################################################################
# READ AN ACCOUNT
######################################################################

@app.route("/accounts/<account_id>")
def read_accounts(account_id):
    """
    Read an Account
    This endpoint will return an Account given the id
    """
    account = Account.find(account_id)
    if account is None:
        abort(status.HTTP_404_NOT_FOUND)
    message = account.serialize()
    return message, status.HTTP_200_OK

######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################

@app.route("/accounts/<account_id>", methods=["PUT"])
def update_accounts(account_id):
    """
    Update an Account
    This endpoint will update an Account given the id and the data in the request's body
    """
    account = Account.find(account_id)
    if account is None:
        abort(status.HTTP_404_NOT_FOUND)
    check_content_type("application/json")
    account.deserialize(request.get_json())
    account.update()
    message = account.serialize()
    return message, status.HTTP_200_OK


######################################################################
# DELETE AN ACCOUNT
######################################################################

@app.route("/accounts/<account_id>", methods=["DELETE"])
def delete_accounts(account_id):
    """
    Delete an Account
    This endpoint will delete an Account given the id
    """
    account = Account.find(account_id)
    if not account is None:
        account.delete()
    return "", status.HTTP_204_NO_CONTENT


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )
