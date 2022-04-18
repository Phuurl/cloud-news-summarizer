# Supporting resources
## Pulumi stack
This stack contains the supporting resources that make up the cloud-news-summarizer.

### Deploy
1. Set up and configure Pulumi - see [their docs](https://www.pulumi.com/docs/get-started/azure/) if you're not sure
2. Create a new stack within this project and set the required config properties - again see [their docs](https://www.pulumi.com/docs/intro/concepts/stack/) if you're unsure
   - Use `pulumi config set <name> <value>` to set the following config items:
     - `azure-native:location` - region to deploy to, this must be one that has support for all the resources in the stack (Cognitive Services is likely to be the most exclusive - I used `westeurope`)
     - `prefix` - a prefix to add to the stack's resource names in Azure, must be alphanumeric and between 1 and 15 characters
3. Deploy the stack (`pulumi up`)
4. Note the output values from the stack, they'll be used in the Function app deployment
