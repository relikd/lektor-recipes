PROJDIR := src
TEXER := lualatex

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
	@cd '$(PROJDIR)' && lektor clean --yes -v

plugins:
	@echo 'Cleaning plugins'
	@cd '$(PROJDIR)' && lektor plugins flush-cache && lektor plugins list

clean-all: clean plugins

# Build

server:
	@cd '$(PROJDIR)' && lektor server # -f ENABLE_PDF_EXPORT

build: dist
	@cd '$(PROJDIR)' && \
	lektor build --output-path ../bin --buildstate-path ../build-state -f ENABLE_PDF_EXPORT # -f ENABLE_APPCACHE
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
	@echo
	@echo 'Generating PDF from tex source ...'
	@echo 'Check if $(TEXER) exists'
	@which $(TEXER)
	@cd extras/pdf-export/ && \
	SECONDS=0; \
	for i in 1 2; do \
		for alt in de en; do \
			fname="pdf-$${alt}.tex"; \
			echo "$$ $(TEXER) $${fname} [$${i}]"; \
			$(TEXER) $${fname} > /dev/null; \
		done; \
	done; \
	echo "done. finished after $${SECONDS}s."
	rm -rf extras/pdf-export/*.{aux,log,out,toc}
	mv extras/pdf-export/pdf-*.pdf bin/static

# Helper methods on all recipes

find-links:
	@echo
	@cd '$(PROJDIR)/content/recipes' && \
	find */*.lr -exec grep --color=auto -i ".\.\./[^ ]*" -o {} + \
	|| echo 'nothing found.'
	@echo
