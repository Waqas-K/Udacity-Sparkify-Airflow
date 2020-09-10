from airflow.hooks.postgres_hook import PostgresHook
from airflow.contrib.hooks.aws_hook import AwsHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

class StageToRedshiftOperator(BaseOperator):
    ui_color = '#358140'
    
    copy_sql =''' COPY {} FROM '{}'
                  ACCESS_KEY_ID '{}'
                  SECRET_ACCESS_KEY '{}'
                  FORMAT as json '{}'
               '''

    @apply_defaults
    def __init__(self,
                 redshift_conn_id='',
                 aws_credentials_id='',
                 s3_bucket='',
                 s3_key='',
                 table='',
                 copy_json_option='auto',
                 *args, **kwargs):

        super(StageToRedshiftOperator, self).__init__(*args, **kwargs)
        self.redshift_conn_id = redshift_conn_id
        self.aws_credentials_id=aws_credentials_id
        self.s3_bucket=s3_bucket
        self.s3_key=s3_key
        self.table=table
        self.copy_json_option=copy_json_option

    def execute(self, context):
        self.log.info('Verifying Credentials and Connections')
        redshift=PostgresHook(postgres_conn_id=self.redshift_conn_id)
        aws_hook=AwsHook(self.aws_credentials_id)
        credentials=aws_hook.get_credentials()
        
        try:
            self.log.info('Deleting destination table')
            redshift.run("DELETE FROM {}".format(self.table))
        except:
            self.log.info('Creating table for the first time')
            
        self.log.info('Copying data to Redshift')
        s3_path='s3://{}/{}'.format(self.s3_bucket,self.s3_key.format(**context))
        copy_sql_formatted = StageToRedshiftOperator.copy_sql.format(
                                                                    self.table,
                                                                    s3_path,
                                                                    credentials.access_key,
                                                                    credentials.secret_key,
                                                                    self.copy_json_option
                                                                    )
        redshift.run(copy_sql_formatted)
        self.log.info('Copy completed to Redshift')