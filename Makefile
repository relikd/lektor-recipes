PROJDIR := src
LEKTOR := lektor --project $(PROJDIR)
BUILD_DIR := $$($(LEKTOR) project-info --output-path)

.PHONY: help
help:
	@echo
	@echo '  dev     - Switch to development branch'
	@echo '  dist    - Switch to distribution branch'
	@echo '  clean   - Removes all temporary server-build files (not ./bin)'
	@echo '  plugins - Clean and rebuild plugin cache'
	@echo
	@echo '  server  - Start lektor server with live change updates'
	@echo '  build   - Build deployable website into ./bin (incl. PDF)'
	@echo '  deploy  - Custom rsync command to sync ./bin to remote server'
	@echo '  pdf     - Generate PDF from tex (not needed if `make build`)'
	@echo
	@echo '  find-links - Search for cross reference between recipes'
	@echo '  find-yield - Print unique `yield:` attribute values'
	@echo '  find-time  - Print unique `time:` attribute values'
	@echo

# Clean

.PHONY: dev
dev:
	@echo Set source to '../../data/development/'
	@rm $(PROJDIR)/content/recipes
	@ln -s '../../data/development/' $(PROJDIR)/content/recipes

.PHONY: dist
dist:
	@echo Set source to '../../data/distribution/'
	@rm $(PROJDIR)/content/recipes
	@ln -s '../../data/distribution/' $(PROJDIR)/content/recipes

.PHONY: clean
clean:
	@echo 'Cleaning output'
	@rm -rf "$(BUILD_DIR)/.lektor/buildstate"*
	@$(LEKTOR) clean --yes -v

.PHONY: plugins
plugins:
	@echo 'Cleaning plugins'
	@$(LEKTOR) plugins flush-cache
	@$(LEKTOR) plugins list

# Build

.PHONY: server
server:
	@$(LEKTOR) server # -f ENABLE_PDF_EXPORT

.PHONY: server-v
server-v:
	@$(LEKTOR) server -v

# --output-path is relative to project file
# --buildstate-path is relative to current working directory
.PHONY: build
build: dist
	@$(LEKTOR) build --output-path ../bin --buildstate-path build-state -f ENABLE_PDF_EXPORT

.PHONY: deploy
deploy:
	@echo
	@echo 'Warning: This will not(!) build but sync all files in ./bin'
	@( read -p "Continue? [y/N]: " sure && case "$$sure" in [yY]) true;; *) false;; esac )
	@echo # --dry-run
	rsync -rclzv --exclude=.lektor --exclude=.DS_Store --delete bin/ vps:/srv/http/recipe-lekture

# technically this isnt needed anymore but it simplyfies latex development
.PHONY: pdf
pdf:
	@SECONDS=0; \
	"$(PROJDIR)/_tex-to-pdf/build_manually.sh" \
	&& echo "done. finished after $${SECONDS}s."

# Helper methods on all recipes

.PHONY: find-links
find-links:
	@echo
	@cd '$(PROJDIR)/content/recipes' && \
	find */*.lr -exec grep --color=auto -i ".\.\./[^ ]*" -o {} + \
	|| echo 'nothing found.'
	@echo

.PHONY: find-dead-links
find-dead-links:
	@echo 'Checking dead links ...'
	@python3 extras/find-dead-links.py 'data/development'

.PHONY: find-yield
find-yield:
	@echo
	@cd '$(PROJDIR)/content/recipes' && \
	find */*.lr -exec grep "^yield: .*" -o {} \; \
	| cut -d' ' -f 2- | tr -d '[0-9-–.]' | sort -u \
	|| echo 'nothing found.'
	@echo

.PHONY: find-time
find-time:
	@cd '$(PROJDIR)/content/recipes' && \
	find */*.lr -exec grep "^time: .*" -o {} \; \
	| cut -d' ' -f 2- | sort -n -u \
	|| echo 'nothing found.'

