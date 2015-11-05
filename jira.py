from errbot import BotPlugin, botcmd
import logging

log = logging.getLogger(name='errbot.plugins.Jira')

try:
    from jira import JIRA, JIRAError
except ImportError:
    log.error("Please install 'jira' python package")


class Jira(BotPlugin):
    """Plugin for Jira"""

    def get_configuration_template(self):
        """ configuration entries """
        config = {
            'api_url': None,
            'api_user': None,
            'api_pass': None,
        }
        return config

    def _login(self):
        username = self.config['api_user']
        password = self.config['api_pass']
        api_url = self.config['api_url']

        try:
            login = JIRA(server=api_url, basic_auth=(username, password))
            self.log.info('logging into {}'.format(api_url))
            return login
        except JIRAError:
            message = 'Unable to login to {}'.format(api_url)
            self.log.info(message)
            return False

    def _check_ticket_passed(self, msg, ticket):

        if ticket == '':
            self.send(msg.frm,
                      'Ticket must be passed',
                      message_type=msg.type,
                      in_reply_to=msg,
                      groupchat_nick_reply=True)
            return False

        return True

    @botcmd(split_args_with=' ')
    def jira(self, msg, args):
        """
        Returns the subject of the ticket along with a link to it.
        """

        ticket = args.pop(0)
        if not self._check_ticket_passed(msg, ticket):
            return

        jira = self._login()

        try:
            issue = jira.issue(ticket)

            response = '{0} created on {1} by {2} ({4}) - {3}'.format(
                issue.fields.summary,
                issue.fields.created,
                issue.fields.reporter.displayName,
                issue.permalink(),
                issue.fields.status.name
            )
        except JIRAError:
            response = 'Ticket {0} not found.'.format(ticket)

        self.send(msg.frm,
                  response,
                  message_type=msg.type,
                  in_reply_to=msg,
                  groupchat_nick_reply=True)

    @botcmd(split_args_with=' ')
    def jira_comment(self, msg, args):
        """
        Adds a comment to a ticket
        Options:
            ticket: jira ticket
            comment: text to add to ticket
        Example
        !jira comment PROJECT-123 I need to revisit this.
        """

        ticket = args.pop(0)
        raw_comment = ' '.join(args)

        if not self._check_ticket_passed(msg, ticket):
            return

        jira = self._login()

        try:
            issue = jira.issue(ticket)
            user = msg.frm
            comment = '{} added: {}'.format(user, raw_comment)
            jira.add_comment(issue, comment)
            response = 'Added comment to {}'.format(ticket)
        except JIRAError:
            response = 'Unable to add comment to {0}.'.format(ticket)

        self.send(msg.frm,
                  response,
                  message_type=msg.type,
                  in_reply_to=msg,
                  groupchat_nick_reply=True)

    @botcmd(split_args_with=' ')
    def jira_reassign(self, msg, args):
        """
        Reassign a ticket to someone else
        Options:
            ticket: jira ticket
            user: user to reassign ticket
        Example
        !jira reassign PROJECT-123 sijis
        """

        ticket = args.pop(0)
        user = args.pop(0)

        if not self._check_ticket_passed(msg, ticket):
            return

        jira = self._login()

        try:
            issue = jira.issue(ticket)
            issue.update(fields={'assignee': {'name':user}})
            response = 'Reassigned {} to {}'.format(ticket, user)
        except JIRAError:
            response = 'Unable to reassign {} to {}'.format(ticket, user)

        self.send(msg.frm,
                  response,
                  message_type=msg.type,
                  in_reply_to=msg,
                  groupchat_nick_reply=True)
