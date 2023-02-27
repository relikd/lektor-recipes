PROJDIR := src
TEXER := lualatex
LEKTOR := lektor --project $(PROJDIR)
BUILD_DIR := $$($(LEKTOR) project-info --output-path)

.PHONY: help dev dist clean plugins clean-all server build deploy pdf-clean pdf find-links

help:
	@echo
	@echo '  dev     - Switch to development branch'
	@echo '  dist    - Switch to distribution branch'
	@echo '  clean   - Removes all temporary server-build files (not ./bin)'
	@echo '  plugins - Clean and rebuild plugin cache'
	@echo '  clean-all - Rebuild everything (not ./bin)'
	@echo
	@echo '  server  - Start lektor server with live change updates'
	@echo '  build   - Build deployable website into ./bin'
	@echo '  deploy  - Custom rsync command to sync ./bin to remote server'
	@echo '  pdf     - Generate PDF from tex (after build)'
	@echo
	@echo '  find-links - Search for cross reference between recipes'
	@echo

define switch_to
	@echo Set source to $(1)
	@rm $(PROJDIR)/content/recipes; ln -s $(1) $(PROJDIR)/content/recipes
endef

# Clean

dev:
	$(call switch_to, '../../data/development/')

dist: 
	$(call switch_to, '../../data/distribution/')

clean:
	@echo 'Cleaning output'
	@rm -rf "$(BUILD_DIR)/.lektor/buildstate"*
	@$(LEKTOR) clean --yes -v

plugins:
	@echo 'Cleaning plugins'
	@$(LEKTOR) plugins flush-cache
	@$(LEKTOR) plugins list

clean-all: clean plugins

# Build

server:
	@$(LEKTOR) server # -f ENABLE_PDF_EXPORT

server-v:
	@$(LEKTOR) server -v

# --output-path is relative to project file
# --buildstate-path is relative to current working directory
build: dist
	@$(LEKTOR) build --output-path ../bin --buildstate-path build-state -f ENABLE_PDF_EXPORT
	@echo
	@echo 'Checking dead links ...'
	@python3 extras/find-dead-links.py

deploy:
	@echo
	@echo 'Warning: This will not(!) build but sync all files in ./bin'
	@( read -p "Continue? [y/N]: " sure && case "$$sure" in [yY]) true;; *) false;; esac )
	@echo # --dry-run
	rsync -rclzv --exclude=.lektor --exclude=.DS_Store --delete bin/ vps:/srv/http/recipe-lekture

pdf:
	@SECONDS=0; \
	"$(PROJDIR)/_tex-to-pdf/build_manually.sh" \
	&& echo "done. finished after $${SECONDS}s."

# Helper methods on all recipes

find-links:
	@echo
	@cd '$(PROJDIR)/content/recipes' && \
	find */*.lr -exec grep --color=auto -i ".\.\./[^ ]*" -o {} + \
	|| echo 'nothing found.'
	@echo

find-yield:
	@echo
	@cd '$(PROJDIR)/content/recipes' && \
	find */*.lr -exec grep "^yield: .*" -o {} \; \
	| cut -d' ' -f 2- | tr -d '[0-9-–.]' | sort -u \
	|| echo 'nothing found.'
	@echo

find-time:
	@cd '$(PROJDIR)/content/recipes' && \
	find */*.lr -exec grep "^time: .*" -o {} \; \
	| cut -d' ' -f 2- | sort -n -u \
	|| echo 'nothing found.'

