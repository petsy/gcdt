package utilities

import groovy.json.JsonSlurper;

public class DpUtilities {

    // "http://169.254.169.254/latest/dynamic/instance-identity/document"
    private static final String METADATA_URL = "http://169.254.169.254/latest/dynamic/instance-identity/document"
    private static final Map accountMap = [644239850139: 'dev', 111537987451: 'preprod', 814767085700: 'prod']
    private static final String TEAM_EMAIL = "team-dp@services.glomex.com"

    public static def getTeamEmail() {
        return TEAM_EMAIL
    }

    public static def getAccountId() throws IOException, MalformedURLException {
        URL url = new URL(METADATA_URL);
        InputStream urlStream = null;

        try {
            urlStream = url.openStream();
            BufferedReader reader = new BufferedReader(new InputStreamReader(urlStream));
            JsonSlurper jsonSlurper = new JsonSlurper();
            Object result = jsonSlurper.parse(reader);
            Map jsonResult = (Map) result;
            String accountid = (String) jsonResult.get("accountId");
            return accountid
        } finally {

        }
    }

    public static def getEnvFromAccountId(String accountId) {

        return accountMap.get(accountId.toLong())
    }

    public static def getEnv() {
        String accountId = getAccountId()
        return getEnvFromAccountId(accountId)
    }

    public static def getBranch() {
        Map branchMap = [dev: "develop", preprod: "develop", prod: "master"]
        String branch = branchMap.get(getEnv())
        return branch
    }

    public static def getSlackChannel() {
        Map channelMap = [dev: "ds-sysmes", preprod: "ds-sysmes-preprod", prod: "ds-sysmes-prod"]
        String channel = channelMap.get(getEnv())
        return channel
    }

}
