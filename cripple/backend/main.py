
import yaml


from xrpl.clients import JsonRpcClient
from flask import Flask, jsonify, request
from xrpl.wallet import generate_faucet_wallet
from xrpl.models.transactions import Payment
from xrpl.utils import xrp_to_drops
from xrpl.transaction import safe_sign_and_autofill_transaction,send_reliable_submission
from xrpl.models.requests.account_info import AccountInfo

app = Flask(__name__)

def xrp_client() -> JsonRpcClient:
    with open('conf.yaml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    JSON_RPC_URL = config['json_rpc_url']
    print(JSON_RPC_URL)
    return JsonRpcClient(JSON_RPC_URL)

@app.route('/xrp/wallet', methods=['POST'])
def generate_xrp_wallet():
    try:
        print('Initiate wallet generation')
        client = xrp_client()
        wallet = generate_faucet_wallet(client, debug=True)

        data = {    
            'status_code': 201,
            'message': 'Successfully generated XRP wallet',
            "data" : {
                "public_key" : wallet.public_key,
                "private_key" : wallet.private_key,
                "classic_address": wallet.classic_address
            }
        }
        return jsonify(data)
    except Exception as e:
        error_data = {
            'status_code': 500,
            'message': 'Error occurred while generating XRP wallet',
            'error': str(e)
        }
        return jsonify(error_data), 500
    

@app.route('/xrp/transactions', methods=['POST'])
def transactions():
    try:
        data = request.get_json()

        user_wallet = data['my_wallet']
        destination_wallet = data['destination_wallet']
        amount = data['amount']

        client = xrp_client()

        my_tx_payment = Payment(
            account=user_wallet,
            amount=xrp_to_drops(amount),
            destination=destination_wallet,
        )

        my_tx_payment_signed = safe_sign_and_autofill_transaction(my_tx_payment, destination_wallet, client)
        tx_response = send_reliable_submission(my_tx_payment_signed, client)
        
        data = {    
            'status_code': 201,
            'message': f'Successfully created a transaction for {destination_wallet}',
            "data" : tx_response
        }
        return jsonify(data)
    except Exception as e:
        error_data = {
            'status_code': 500,
            'message': 'Error occurred while generating XRP wallet',
            'error': str(e)
        }
        return jsonify(error_data), 500


@app.route('/xrp/wallet/<string:address>/history', methods=['GET'])
def get_transaction_history(address : str):
    try:
        acct_info = AccountInfo(
            account=address,
            ledger_index="validated",
            strict=True,
        )
        client = xrp_client()

        response = client.request(acct_info)
        result = response.result
        print("response.status: ", response.status)
        
        data = {    
            'status_code': 201,
            'message': f'Succesfully received transactions',
            "data" : result
        }
        return jsonify(data)
    except Exception as e:
        error_data = {
            'status_code': 500,
            'message': 'Error occurred while generating XRP wallet',
            'error': str(e)
        }
        return jsonify(error_data), 500


if __name__ == '__main__':
    app.run()